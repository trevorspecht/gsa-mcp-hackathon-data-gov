import pytest
from pydantic import ValidationError

from datagov_mcp.agent import AgentSettings, answer_text, tool_specs
from datagov_mcp.config import Settings


@pytest.mark.parametrize(
    "name", ["databricks_catalog", "databricks_schema", "databricks_table"]
)
def test_identifiers_cannot_escape_query(name):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{name: "x`; DROP TABLE other; --"})


@pytest.mark.parametrize(
    "host",
    [
        "http://example.com",
        "https://user@example.com",
        "https://example.com/api",
        "https://example.com?token=value",
        "https://example.com:1234",
    ],
)
def test_workspace_origin_validation(host):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, databricks_host=host)


def test_bare_app_injected_host_is_normalized():
    settings = Settings(_env_file=None, databricks_host="dbc-1.cloud.databricks.com")
    assert settings.databricks_host == "https://dbc-1.cloud.databricks.com"


def test_agent_url_requires_tls_and_mcp_path():
    with pytest.raises(ValidationError):
        AgentSettings(_env_file=None, databricks_mcp_url="http://example.com/mcp")
    with pytest.raises(ValidationError):
        AgentSettings(_env_file=None, databricks_mcp_url="https://example.com/other")


async def test_agent_tool_definitions_preserve_mcp_schema(settings):
    from fastmcp import Client

    from datagov_mcp.app import create_server

    async with Client(create_server(settings)) as client:
        specs = tool_specs(await client.list_tools())
    search = next(
        s["function"]
        for s in specs
        if s["function"]["name"] == "find_data_for_question"
    )
    assert "request" in search["parameters"]["properties"]


def test_answer_text_drops_reasoning_parts():
    parts = [{"type": "reasoning", "summary": []}, {"type": "text", "text": "Answer"}]
    assert answer_text(parts) == "Answer"
    assert answer_text("plain") == "plain"
