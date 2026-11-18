import json
import sqlite3

import pytest
from pydantic import ValidationError

from datagov_mcp.analytics import shape_rows
from datagov_mcp.errors import ServiceError
from datagov_mcp.evidence import EvidenceStore
from datagov_mcp.models import CompareRequest
from datagov_mcp.registry import Registry, asset


def test_real_sql_numeric_reference_and_missing_county():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute(
        "CREATE TABLE indicators (county_fips TEXT, county_name TEXT, "
        "state_fips TEXT, year INTEGER, population INTEGER, "
        "unemployment_rate REAL, snapshot_id TEXT)"
    )
    db.executemany(
        "INSERT INTO indicators VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("24001", "Example A", "24", 2022, 100, 6.0, "snapshot"),
            ("24001", "Example A", "24", 2024, 125, 4.5, "snapshot"),
            ("24003", "Example B", "24", 2022, 200, 3.0, "snapshot"),
        ],
    )
    rows = [
        dict(row)
        for row in db.execute(
            asset("compare.sql").format(table="indicators"),
            {
                "state": "24",
                "start_year": 2022,
                "end_year": 2024,
                "snapshot": "snapshot",
            },
        )
    ]
    result = shape_rows(
        rows,
        CompareRequest(
            population_direction="increase", unemployment_direction="decrease"
        ),
        ["24001", "24003"],
    )
    assert result["rows"][0]["population_change"] == 25.0
    assert result["rows"][0]["unemployment_change"] == -1.5
    assert result["missing_counties"] == ["24003"]
    assert result["summary"]["counties_compared"] == 1
    db.close()


def test_summary_counts_ignore_filters_and_limit():
    def row(county, pop_change, rate_change):
        return {
            "county_fips": county,
            "county_name": county,
            "population_start": 100.0,
            "population_end": 100.0 + pop_change,
            "population_change": pop_change,
            "unemployment_start": 3.1,
            "unemployment_end": 3.1 + rate_change,
            "unemployment_change": rate_change,
        }

    rows = [
        row("24001", 1.0, 3.3 - 3.1),
        row("24003", -1.0, 0.5),
        row("24005", 2.0, -0.3),
        row("24009", 0.5, 2.6 - 2.6),
    ]
    request = CompareRequest(population_direction="decrease", limit=1)
    result = shape_rows(rows, request, [r["county_fips"] for r in rows])
    summary = result["summary"]
    assert result["matched_count"] == 1
    assert summary["counties_compared"] == 4
    assert summary["population"] == {"increased": 3, "decreased": 1, "unchanged": 0}
    assert summary["unemployment_rate"] == {"rose": 2, "fell": 1, "unchanged": 1}
    assert summary["population_by_unemployment"]["increased"] == {
        "rose": 1,
        "fell": 1,
        "unchanged": 1,
    }


def test_unknown_metrics_and_periods_decline(settings):
    registry = Registry(settings)
    result = registry.assess(CompareRequest(metric_ids=["population", "ad_spend"]))
    assert result["status"] == "unsupported"
    assert not registry.assess(CompareRequest(start_year=2020))["compatible"]
    assert not registry.assess(CompareRequest(state_fips="06"))["compatible"]
    assert registry.assess(CompareRequest())["status"] == "setup_required"


def test_unreviewed_manifest_does_not_enable_queries(settings):
    settings.analytics_manifest.write_text(json.dumps({"domain_reviewed": False}))
    assert not Registry(settings).assess(CompareRequest())["ready_to_execute"]


@pytest.mark.parametrize(
    "values",
    [
        {"start_year": 2024, "end_year": 2022},
        {"county_fips": ["06001"]},
        {"metric_ids": ["population", "population"]},
        {"county_fips": ["24001", "24001"]},
    ],
)
def test_comparison_input_boundaries(values):
    with pytest.raises(ValidationError):
        CompareRequest(**values)


def test_evidence_roundtrip_and_path_boundary(tmp_path):
    store = EvidenceStore(tmp_path)
    identifier = store.save({"result": {"rows": []}})
    assert store.get(identifier)["result"] == {"rows": []}
    with pytest.raises(ServiceError):
        store.get("../../.env")


def test_duplicate_warehouse_grain_rejected():
    row = {"county_fips": "24001"}
    with pytest.raises(ServiceError, match="duplicate"):
        shape_rows([row, row], CompareRequest(), ["24001"])
