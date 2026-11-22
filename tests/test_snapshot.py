import json

import pytest

from datagov_mcp.ingestion import COUNTIES
from datagov_mcp.registry import Registry
from datagov_mcp.snapshot import Manifest


def manifest_data():
    return {
        "snapshot_id": "a" * 24,
        "state_fips": "24",
        "years": [2022, 2023, 2024],
        "county_fips": sorted(COUNTIES),
        "row_count": 72,
        "domain_reviewed": True,
        "data_sha256": "b" * 64,
        "sources": [
            {"id": name, "url": "https://example.com", "sha256": "c" * 64}
            for name in ("census_population", "bls_laus")
        ],
    }


def test_duplicate_counties_and_missing_years_rejected():
    data = manifest_data()
    data["county_fips"][-1] = data["county_fips"][0]
    with pytest.raises(ValueError):
        Manifest.model_validate(data)
    data = manifest_data()
    data["years"] = [2022, 2022, 2024]
    with pytest.raises(ValueError):
        Manifest.model_validate(data)


def test_valid_manifest_without_load_is_not_ready(settings):
    settings.analytics_manifest.write_text(json.dumps(manifest_data()))
    registry = Registry(settings)
    manifest, blocker = registry.manifest()
    assert manifest and blocker is None
    from datagov_mcp.datasets import Datasets
    from datagov_mcp.evidence import EvidenceStore

    datasets = Datasets(settings, None, EvidenceStore(settings.evidence_dir))
    state = datasets.readiness(datasets.get("md_county_population_unemployment"))
    assert not state["ready"]
    assert (
        "Snapshot is not verified loaded in the configured table" in state["blockers"]
    )
