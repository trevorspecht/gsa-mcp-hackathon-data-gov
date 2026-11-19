import json
from types import SimpleNamespace

from fastmcp import Client

from datagov_mcp.app import create_server
from datagov_mcp.ingestion import COUNTIES


async def test_ready_comparison_calls_fixed_sql_and_retrieves_evidence(settings):
    settings.databricks_host = "https://workspace.example.com"
    settings.databricks_warehouse_id = "warehouse"
    settings.databricks_catalog = "curated"
    settings.databricks_schema = "public_data"
    settings.databricks_client_id = "test-client"
    from pydantic import SecretStr

    settings.databricks_client_secret = SecretStr("synthetic-test-value")
    manifest = {
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
    settings.analytics_manifest.write_text(json.dumps(manifest))
    from datagov_mcp.models import CompareRequest
    from datagov_mcp.registry import Registry

    registry = Registry(settings)
    assessment = registry.assess(CompareRequest())
    assert assessment["ready_to_execute"]
    assert all("domain reviewed" in s["verification"] for s in assessment["sources"])
    assert all(s["sha256"] == "c" * 64 for s in assessment["sources"])
    assert "awaiting" in registry.data["sources"][0]["verification"]
    assert registry.capabilities()["registry"]["sources"] == assessment["sources"]
    calls = []

    def execute(sql, parameters):
        calls.append((sql, parameters))
        return {
            "query_id": "synthetic-query",
            "rows": [
                {
                    "county_fips": "24510",
                    "county_name": "Synthetic city",
                    "population_start": "100",
                    "population_end": "125",
                    "population_change": "25",
                    "unemployment_start": "6",
                    "unemployment_end": "4.5",
                    "unemployment_change": "-1.5",
                }
            ],
        }

    server = create_server(settings, warehouse=SimpleNamespace(execute=execute))
    async with Client(server) as client:
        result = await client.call_tool(
            "compare_public_indicators", {"request": {"county_fips": ["24510"]}}
        )
        assert result.data["status"] == "complete"
        assert result.data["rows"][0]["population_change"] == 25
        evidence = await client.call_tool(
            "get_analysis_evidence", {"evidence_id": result.data["evidence_id"]}
        )
        assert evidence.data["query_id"] == "synthetic-query"
        assert evidence.data["snapshot"]["snapshot_id"] == "a" * 24
    assert ":start_year" in calls[0][0]
    assert calls[0][1]["start_year"] == 2022
