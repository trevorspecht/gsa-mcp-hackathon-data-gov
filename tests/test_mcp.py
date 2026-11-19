import httpx
from fastmcp import Client

from datagov_mcp.app import create_server


async def test_registered_protocol_tools_resources_and_setup_response(settings):
    server = create_server(
        settings,
        httpx.MockTransport(
            lambda r: httpx.Response(
                200,
                json={"results": [{"title": "Water quality", "identifier": "water"}]},
            )
        ),
    )
    async with Client(server) as client:
        tools = await client.list_tools()
        assert {t.name for t in tools} == {
            "find_data_for_question",
            "inspect_dataset",
            "suggest_search_filters",
            "assess_comparison",
            "compare_public_indicators",
            "get_analysis_evidence",
            "inspect_science_capabilities",
            "query_science_series",
        }
        result = await client.call_tool(
            "find_data_for_question", {"request": {"query": "water"}}
        )
        assert result.data["datasets"][0]["title"] == "Water quality"
        status = await client.call_tool("compare_public_indicators", {"request": {}})
        assert status.data["status"] == "setup_required"
        resources = await client.list_resources()
        assert any(str(r.uri) == "data.gov://capabilities" for r in resources)
        assert await client.read_resource("data.gov://capabilities")


async def test_mcp_upstream_error_is_structured(settings):
    server = create_server(settings, httpx.MockTransport(lambda r: httpx.Response(429)))
    async with Client(server) as client:
        result = await client.call_tool(
            "find_data_for_question", {"request": {"query": "water"}}
        )
        assert result.data["error"]["code"] == "UPSTREAM_RATE_LIMIT"
