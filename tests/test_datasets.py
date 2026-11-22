import json
import sqlite3

import httpx
import pytest
from fastmcp import Client
from pydantic import SecretStr, ValidationError

from datagov_mcp.app import create_server
from datagov_mcp.ingestion import COUNTIES
from datagov_mcp.models import ChangeRequest, CompatibilityRequest, ObservationRequest


def ready_settings(settings):
    settings.databricks_host = "https://workspace.example.com"
    settings.databricks_warehouse_id = "warehouse"
    settings.databricks_catalog = "curated"
    settings.databricks_schema = "public_data"
    settings.databricks_client_id = "test-client"
    settings.databricks_client_secret = SecretStr("synthetic-test-value")
    settings.analytics_manifest.write_text(
        json.dumps(
            {
                "snapshot_id": "a" * 24,
                "state_fips": "24",
                "years": [2022, 2023, 2024],
                "county_fips": sorted(COUNTIES),
                "row_count": 72,
                "domain_reviewed": True,
                "data_sha256": "b" * 64,
                "loaded_table": settings.table_name,
                "sources": [
                    {"id": name, "url": "https://example.com", "sha256": "c" * 64}
                    for name in ("census_population", "bls_laus")
                ],
            }
        )
    )
    return settings


class SqliteWarehouse:
    """Executes generated SQL against SQLite to verify the real statement text."""

    def __init__(self, rows):
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute(
            "CREATE TABLE indicators (county_fips TEXT, county_name TEXT, "
            "state_fips TEXT, year INTEGER, population INTEGER, "
            "unemployment_rate REAL, snapshot_id TEXT)"
        )
        self.db.executemany("INSERT INTO indicators VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
        self.calls = []

    def execute(self, sql, parameters):
        self.calls.append((sql, parameters))
        local = sql.replace("`curated`.`public_data`.`county_indicators`", "indicators")
        return {
            "query_id": "q",
            "rows": [dict(r) for r in self.db.execute(local, parameters)],
        }


def rows():
    return [
        ("24001", "A", "24", 2022, 100, 6.0, "a" * 24),
        ("24001", "A", "24", 2024, 125, 4.5, "a" * 24),
        ("24003", "B", "24", 2022, 200, 3.0, "a" * 24),
        ("24005", "C", "24", 2022, 300, 3.1, "a" * 24),
        ("24005", "C", "24", 2024, 290, 3.3, "a" * 24),
        ("24005", "C", "24", 2023, 295, 3.2, "b" * 24),
    ]


async def test_generic_change_over_warehouse_sql(settings):
    warehouse = SqliteWarehouse(rows())
    server = create_server(ready_settings(settings), warehouse=warehouse)
    async with Client(server) as client:
        result = (
            await client.call_tool(
                "analyze_change",
                {
                    "request": {
                        "dataset_id": "md_county_population_unemployment",
                        "start_period": 2022,
                        "end_period": 2024,
                        "geography_ids": ["24001", "24003", "24005"],
                        "direction_filters": {"population": "increase"},
                    }
                },
            )
        ).data
        assert result["status"] == "complete"
        assert [r["geography_id"] for r in result["rows"]] == ["24001"]
        row = result["rows"][0]
        assert row["population_change"] == 25.0
        assert row["unemployment_rate_change"] == -1.5
        assert result["missing_geographies"] == ["24003"]
        summary = result["summary"]
        assert summary["geographies_compared"] == 2
        assert summary["directions"]["population"]["decreased"] == 1
        units = {m["id"]: m["change_unit"] for m in result["measures"]}
        assert units == {
            "population": "percent",
            "unemployment_rate": "percentage points",
        }
        evidence = (
            await client.call_tool(
                "get_analysis_evidence", {"evidence_id": result["evidence_id"]}
            )
        ).data
        assert evidence["observation_provenance"]["query_id"] == "q"
    sql, parameters = warehouse.calls[0]
    assert ":snapshot" in sql and parameters["snapshot"] == "a" * 24
    assert "24001" not in sql and "2022" not in sql


async def test_packaged_dataset_query_and_change(settings):
    async with Client(create_server(settings)) as client:
        series = (
            await client.call_tool(
                "query_dataset",
                {"request": {"dataset_id": "chesapeake_conservation_tillage"}},
            )
        ).data
        assert [r["period"] for r in series["rows"]] == [1985, 1992, 2002, 2012]
        change = (
            await client.call_tool(
                "analyze_change",
                {
                    "request": {
                        "dataset_id": "chesapeake_cover_crops",
                        "start_period": 2002,
                        "end_period": 2012,
                    }
                },
            )
        ).data
        assert change["rows"][0]["cover_crop_area_change"] == 1289.0575
        gap = (
            await client.call_tool(
                "analyze_change",
                {
                    "request": {
                        "dataset_id": "chesapeake_cover_crops",
                        "start_period": 2002,
                        "end_period": 2005,
                    }
                },
            )
        ).data
        assert gap["status"] == "unsupported"


async def test_unregistered_and_unready_requests_fail_closed(settings):
    async with Client(create_server(settings)) as client:
        unknown = (
            await client.call_tool(
                "query_dataset", {"request": {"dataset_id": "private_table"}}
            )
        ).data
        assert unknown["error"]["code"] == "UNKNOWN_DATASET"
        measure = (
            await client.call_tool(
                "query_dataset",
                {
                    "request": {
                        "dataset_id": "md_annual_temperature",
                        "measure_ids": ["ad_spend"],
                    }
                },
            )
        ).data
        assert measure["error"]["code"] == "UNKNOWN_MEASURE"
        setup = (
            await client.call_tool(
                "query_dataset",
                {"request": {"dataset_id": "md_county_population_unemployment"}},
            )
        ).data
        assert setup["status"] == "setup_required"
        place = (
            await client.call_tool(
                "query_dataset",
                {
                    "request": {
                        "dataset_id": "md_annual_temperature",
                        "geography_ids": ["06"],
                    }
                },
            )
        ).data
        assert place["status"] == "unsupported"


@pytest.mark.parametrize(
    "request_data",
    [
        {"dataset_id": "x; DROP TABLE"},
        {"dataset_id": "valid", "geography_ids": ["24001'--"]},
        {"dataset_id": "valid", "start_period": 2012, "end_period": 2000},
        {"dataset_id": "valid", "unexpected": "field"},
    ],
)
def test_request_schemas_reject_unsafe_values(request_data):
    with pytest.raises(ValidationError):
        ObservationRequest(**request_data)


def test_change_and_compatibility_schema_bounds():
    with pytest.raises(ValidationError):
        ChangeRequest(dataset_id="x", start_period=2024, end_period=2022)
    with pytest.raises(ValidationError):
        ChangeRequest(
            dataset_id="x",
            start_period=2022,
            end_period=2024,
            measure_ids=["a"],
            direction_filters={"b": "increase"},
        )
    with pytest.raises(ValidationError):
        CompatibilityRequest(datasets=[{"dataset_id": "x"}])


async def test_compatibility_is_generic_geography_and_period_logic(settings):
    async with Client(create_server(settings)) as client:
        result = (
            await client.call_tool(
                "assess_compatibility",
                {
                    "request": {
                        "datasets": [
                            {"dataset_id": "md_annual_temperature"},
                            {"dataset_id": "md_annual_precipitation"},
                            {"dataset_id": "chesapeake_cover_crops"},
                        ]
                    }
                },
            )
        ).data
    status = {tuple(p["datasets"]): p["status"] for p in result["pairs"]}
    assert (
        status[("md_annual_temperature", "md_annual_precipitation")]
        == "descriptive_alignment_possible"
    )
    assert (
        status[("md_annual_temperature", "chesapeake_cover_crops")] == "not_comparable"
    )


def climate_csv(units="Degrees Fahrenheit"):
    lines = "\n".join(f"{year}12,50.0" for year in range(1985, 2013))
    return f"# Units: {units}\nDate,Value\n{lines}\n".encode()


async def test_live_refresh_uses_only_registered_route(settings):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(200, content=climate_csv())

    server = create_server(settings, publisher_transport=httpx.MockTransport(handler))
    async with Client(server) as client:
        result = (
            await client.call_tool(
                "query_dataset",
                {
                    "request": {"dataset_id": "md_annual_temperature"},
                    "live": True,
                },
            )
        ).data
    assert result["provenance"]["storage"] == "Live publisher file"
    assert len(result["rows"]) == 28
    assert calls == [
        "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/"
        "statewide/time-series/18/tavg/12/12/1985-2012.csv"
    ]


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(302, headers={"location": "https://evil.example/"}),
        httpx.Response(200, content=b"x" * 100_001),
        httpx.Response(200, content=climate_csv("Inches")),
    ],
)
async def test_live_refresh_failures_are_structured(settings, response):
    server = create_server(
        settings, publisher_transport=httpx.MockTransport(lambda r: response)
    )
    async with Client(server) as client:
        result = (
            await client.call_tool(
                "query_dataset",
                {
                    "request": {"dataset_id": "md_annual_temperature"},
                    "live": True,
                },
            )
        ).data
    assert result["error"]["code"].startswith("UPSTREAM_")
