import json
from types import SimpleNamespace

import httpx
import pytest
from fastmcp import Client as MCPClient

from datagov_mcp import agent
from datagov_mcp.app import create_server


def test_request_protocols_and_statuses():
    settings = agent.AgentSettings(_env_file=None, agent_api="responses")
    tool = {"type": "function", "function": {"name": "test", "parameters": {}}}
    path, body = agent.model_request(settings, [], [tool])
    assert path == "/ai-gateway/openai/v1/responses"
    assert body["tools"][0]["strict"] is False
    assert body["max_output_tokens"] == 4000
    assert "store" not in body and "previous_response_id" not in body
    payload = {
        "status": "incomplete",
        "incomplete_details": {"reason": "max_output_tokens"},
        "output": [],
    }
    _, _, _, complete, metadata = agent.parse_turn(payload, "responses")
    assert (
        not complete and metadata["incomplete_details"]["reason"] == "max_output_tokens"
    )
    settings.agent_api = "chat"
    path, body = agent.model_request(settings, [], [tool])
    assert path.endswith("/invocations") and body["max_tokens"] == 4000
    payload = {
        "choices": [
            {
                "finish_reason": "length",
                "message": {"role": "assistant", "content": "cut off"},
            }
        ]
    }
    assert not agent.parse_turn(payload, "chat")[3]
    payload["choices"][0]["finish_reason"] = "stop"
    assert agent.parse_turn(payload, "chat")[3]


async def test_responses_loop_preserves_items_and_tool_call_id(settings, monkeypatch):
    server = create_server(settings)
    monkeypatch.setattr(agent, "Client", lambda *a, **kw: MCPClient(server))
    calls = []

    def handle(request):
        body = json.loads(request.content)
        calls.append(body)
        if len(calls) == 1:
            return httpx.Response(
                200,
                json={
                    "status": "completed",
                    "output": [
                        {"type": "reasoning", "id": "reason", "summary": []},
                        {
                            "type": "function_call",
                            "call_id": "call1",
                            "name": "assess_comparison",
                            "arguments": '{"request":{}}',
                        },
                    ],
                },
            )
        assert body["input"][-1]["type"] == "function_call_output"
        assert body["input"][-1]["call_id"] == "call1"
        assert body["input"][2]["type"] == "reasoning"
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "Needs setup."}],
                    }
                ],
            },
        )

    original = httpx.AsyncClient
    monkeypatch.setattr(
        agent.httpx,
        "AsyncClient",
        lambda **kw: original(transport=httpx.MockTransport(handle)),
    )
    config = agent.AgentSettings(
        _env_file=None,
        agent_api="responses",
        databricks_host="https://example.com",
        databricks_mcp_url="https://example.com/mcp",
    )
    workspace = SimpleNamespace(config=SimpleNamespace(authenticate=lambda: {}))
    result = await agent.run_agent("Check readiness", config, workspace)
    assert result["status"] == "complete" and result["answer"] == "Needs setup."
    assert len(result["trace"]) == 1 and len(result["model_turns"]) == 2


async def test_incomplete_turn_never_executes_tools(settings, monkeypatch):
    monkeypatch.setattr(
        agent, "Client", lambda *a, **kw: MCPClient(create_server(settings))
    )

    async def incomplete(*args):
        return (
            [],
            [{"id": "x", "function": {"name": "assess_comparison", "arguments": "{}"}}],
            "partial",
            False,
            {"status": "incomplete"},
        )

    monkeypatch.setattr(agent, "model_turn", incomplete)
    config = agent.AgentSettings(
        _env_file=None, databricks_mcp_url="https://example.com/mcp"
    )
    workspace = SimpleNamespace(config=SimpleNamespace(authenticate=lambda: {}))
    result = await agent.run_agent("Check", config, workspace)
    assert result["status"] == "incomplete" and result["trace"] == []


@pytest.mark.parametrize("api", ["responses", "chat"])
async def test_unknown_tool_rejected(settings, monkeypatch, api):
    monkeypatch.setattr(
        agent, "Client", lambda *a, **kw: MCPClient(create_server(settings))
    )

    async def unknown(*args):
        return (
            [],
            [{"id": "x", "function": {"name": "execute_sql", "arguments": "{}"}}],
            "",
            True,
            {},
        )

    monkeypatch.setattr(agent, "model_turn", unknown)
    config = agent.AgentSettings(
        _env_file=None, agent_api=api, databricks_mcp_url="https://example.com/mcp"
    )
    workspace = SimpleNamespace(config=SimpleNamespace(authenticate=lambda: {}))
    with pytest.raises(ValueError, match="Unknown tool"):
        await agent.run_agent("Check", config, workspace)


async def test_cli_incomplete_exit_preserves_partial_result(monkeypatch, capsys):
    import sys

    monkeypatch.setattr(sys, "argv", ["datagov-agent", "Check readiness"])
    monkeypatch.setattr(agent, "agent_workspace", lambda settings: None)
    monkeypatch.setattr(agent, "run_agent", lambda *args: None)
    monkeypatch.setattr(
        agent.asyncio,
        "run",
        lambda value: {
            "status": "incomplete",
            "answer": "partial answer",
            "trace": [],
            "model_turns": [{"status": "incomplete"}],
        },
    )
    with pytest.raises(SystemExit) as exc:
        agent.main()
    assert exc.value.code == 2
    assert json.loads(capsys.readouterr().out)["answer"] == "partial answer"
