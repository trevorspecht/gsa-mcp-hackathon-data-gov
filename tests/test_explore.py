import httpx
import pytest

from datagov_mcp.evidence import EvidenceStore
from datagov_mcp.tools.explore import ExploreRequest, explore, parse_climate


def raw():
    return (
        "# Units: Degrees Fahrenheit\nDate,Value\n"
        + "\n".join(f"{year}12,50.0" for year in range(1985, 2013))
    ).encode()


async def test_preview_live_fixed_source_and_snapshot(tmp_path):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(200, content=raw())

    result = await explore(
        ExploreRequest(dataset_ids=["md_temperature", "chesapeake_cover_crops"]),
        EvidenceStore(tmp_path),
        httpx.MockTransport(handler),
    )
    assert result["status"] == "complete"
    assert len(calls) == 1 and calls[0].startswith("https://www.ncei.noaa.gov/")
    assert result["datasets"][0]["retrieval"] == "live publisher file"
    assert len(result["datasets"][0]["rows"]) == 28
    assert "snapshot" in result["datasets"][1]["retrieval"]
    assert result["compatibility"]["pairs"][0]["status"] == "not_comparable"
    assert not result["compatibility"]["pairs"][0]["same_geography"]


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(302, headers={"location": "https://evil.example/data"}),
        httpx.Response(200, content=b"x" * 100001),
        httpx.Response(200, content=b"invalid"),
    ],
)
async def test_preview_failures_are_retained(tmp_path, response):
    result = await explore(
        ExploreRequest(dataset_ids=["md_temperature", "chesapeake_cover_crops"]),
        EvidenceStore(tmp_path),
        httpx.MockTransport(lambda r: response),
    )
    assert result["status"] == "partial"
    assert result["datasets"][0]["status"] == "failed"
    assert result["datasets"][1]["status"] == "complete"


def test_invalid_ids_and_coverage():
    with pytest.raises(ValueError):
        ExploreRequest(dataset_ids=["http://localhost/data"])
    with pytest.raises(ValueError):
        parse_climate(raw().replace(b"198512", b"198511"), "md_temperature")
    with pytest.raises(ValueError):
        parse_climate(raw().replace(b"50.0", b"nan"), "md_temperature")
