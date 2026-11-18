import httpx
import pytest

from datagov_mcp.catalog import Catalog
from datagov_mcp.errors import ServiceError
from datagov_mcp.http import CatalogHTTP
from datagov_mcp.models import SearchRequest


def response(request):
    return httpx.Response(
        200,
        json={
            "results": [
                {
                    "identifier": "https://publisher.example/dataset",
                    "title": "Population",
                    "harvest_record": "https://catalog.data.gov/harvest_record/ff0bdb27-0390-429e-a1ec-649b0d7921d8",
                    "dcat": {
                        "identifier": "https://publisher.example/dataset",
                        "accessRights": "public",
                    },
                }
            ],
            "after": "opaque-upstream-cursor",
        },
    )


async def test_cursor_bound_to_filters_and_three_page_budget(settings):
    calls = []

    def handler(request):
        calls.append(request)
        return response(request)

    catalog = Catalog(CatalogHTTP(settings, httpx.MockTransport(handler)))
    first = await catalog.search(SearchRequest(query="population"))
    assert first["datasets"][0]["identifier"].startswith("https://")
    with pytest.raises(ServiceError, match="Filters changed"):
        await catalog.search(
            SearchRequest(query="housing", cursor=first["next_cursor"])
        )
    second = await catalog.search(
        SearchRequest(query="population", cursor=first["next_cursor"])
    )
    third = await catalog.search(
        SearchRequest(query="population", cursor=second["next_cursor"])
    )
    assert third["next_cursor"] is None and third["page_budget_reached"]
    assert calls[1].url.params["after"] == "opaque-upstream-cursor"


async def test_cache_and_hourly_budget(settings):
    settings.catalog_requests_per_hour = 1
    client = CatalogHTTP(settings, httpx.MockTransport(response))
    await client.get("/search", {"q": "water"})
    _, meta = await client.get("/search", {"q": "water"})
    assert meta["cache_hit"]
    with pytest.raises(ServiceError) as error:
        await client.get("/search", {"q": "housing"})
    assert error.value.code == "LOCAL_RATE_LIMIT"


@pytest.mark.parametrize("status", [302, 403, 404, 429, 500])
async def test_errors_do_not_leak_upstream_bodies(settings, status):
    client = CatalogHTTP(
        settings,
        httpx.MockTransport(
            lambda r: httpx.Response(status, text="private-upstream-detail")
        ),
    )
    with pytest.raises(ServiceError) as error:
        await client.get("/search")
    assert "private-upstream" not in str(error.value.as_dict())


async def test_oversized_response_and_non_json(settings):
    for response in (
        httpx.Response(200, text="html"),
        httpx.Response(
            200, content=b" " * 5_000_001, headers={"content-type": "application/json"}
        ),
    ):
        client = CatalogHTTP(settings, httpx.MockTransport(lambda r: response))
        with pytest.raises(ServiceError):
            await client.get("/search")


@pytest.mark.parametrize(
    "path", ["//evil.example", "/../secret", "/%2e%2e/a", "https://evil.example"]
)
async def test_no_arbitrary_destination(settings, path):
    client = CatalogHTTP(settings)
    with pytest.raises(ServiceError):
        await client.get(path)


async def test_raw_harvest_fallback_and_distribution_rights(settings):
    client = Catalog(
        CatalogHTTP(
            settings,
            httpx.MockTransport(
                lambda r: httpx.Response(
                    200,
                    json={
                        "source_transform": None,
                        "source_raw": {
                            "title": "Example",
                            "accessLevel": "public",
                            "distribution": [
                                {
                                    "downloadURL": "https://publisher.example/file.csv",
                                    "accessRights": "restricted public",
                                    "license": "publisher-specific",
                                }
                            ],
                        },
                    },
                )
            ),
        )
    )
    data = await client.inspect("ff0bdb27-0390-429e-a1ec-649b0d7921d8")
    assert data["metadata_form"] == "raw"
    assert (
        data["dataset"]["distributions"][0]["terms"]["accessRights"]
        == "restricted public"
    )
    assert not data["dataset"]["queryable"]
