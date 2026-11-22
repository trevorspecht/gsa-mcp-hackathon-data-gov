import httpx
from fastmcp import Client

from datagov_mcp.app import create_server
from datagov_mcp.datasets import Datasets
from datagov_mcp.evidence import EvidenceStore
from datagov_mcp.readiness import assess, ranked

NOAA = "https://data.noaa.gov/waf/NOAA/NESDIS/ncei/aim/iso/xml/C00005.xml"


def registry(settings):
    return Datasets(settings, None, EvidenceStore(settings.evidence_dir))


def test_advertised_download_is_not_ready(settings):
    result = assess(
        {
            "identifier": "unknown",
            "access_status": "public_metadata_claim",
            "distributions": [
                {
                    "download_url": "https://example.gov/data.csv",
                    "format": "CSV",
                    "byte_size": "1000",
                }
            ],
        },
        registry(settings),
    )
    assert result["status"] == "access_unverified"
    assert result["estimated_wait_seconds"] is None
    assert not result["advertised_routes"][0]["verified"]


def test_exact_science_parent_binding_exposes_only_reviewed_scopes(settings):
    result = assess({"identifier": NOAA}, registry(settings))
    assert result["status"] == "ready_within_reviewed_scope"
    assert {scope["dataset_id"] for scope in result["scopes"]} == {
        "md_annual_temperature",
        "md_annual_precipitation",
    }
    assert result["question_compatibility"].startswith("Not established")
    unbound = assess(
        {"identifier": "different", "title": "Maryland annual average temperature"},
        registry(settings),
    )
    assert unbound["status"] == "metadata_only"


def test_county_binding_requires_loaded_destination(settings):
    result = assess({"identifier": "DOL-BLS-3060-01"}, registry(settings))
    assert result["status"] == "setup_required"
    assert result["scopes"][0]["dataset_id"] == "md_county_population_unemployment"
    assert result["blockers"]


def test_restricted_route_requires_review(settings):
    result = assess(
        {
            "access_status": "restricted",
            "distributions": [{"access_url": "https://example.gov/api"}],
        },
        registry(settings),
    )
    assert result["status"] == "setup_required"


def test_ranking_is_relevance_not_readiness_and_deduplicates(settings):
    datasets = [
        {"identifier": NOAA, "title": "Climate", "harvest_record_id": "a"},
        {
            "identifier": "water",
            "title": "Water quality Maryland",
            "harvest_record_id": "b",
        },
        {"identifier": "water", "title": "Duplicate", "harvest_record_id": "c"},
    ]
    result = ranked(
        "Find Maryland water quality datasets", datasets, registry(settings)
    )
    assert len(result) == 2
    assert result[0]["identifier"] == "water"
    assert not result[0]["queryable"]
    assert result[1]["queryable"]
    assert result[0]["candidate_rank"] == 1


async def test_readiness_mcp_fetches_only_fixed_catalog_metadata(settings):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(
            200,
            json={
                "source_raw": {
                    "identifier": "unknown",
                    "title": "Water quality",
                    "distribution": [
                        {"downloadURL": "https://untrusted.example/file.csv"}
                    ],
                }
            },
        )

    server = create_server(settings, httpx.MockTransport(handler))
    async with Client(server) as client:
        result = await client.call_tool(
            "assess_dataset_readiness",
            {
                "question": "Water quality",
                "harvest_record_ids": ["ff0bdb27-0390-429e-a1ec-649b0d7921d8"],
            },
        )
        assert result.data["datasets"][0]["readiness"]["status"] == "access_unverified"
        assert len(calls) == 1
        assert calls[0].startswith("https://catalog.data.gov/harvest_record/")
