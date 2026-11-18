"""Real stdio MCP subprocess checks; records actual outputs, not mocked passes."""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def main():
    root = Path(__file__).resolve().parents[1]
    transcript = {"started_at": datetime.now(timezone.utc).isoformat(), "steps": []}
    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "datagov_mcp.app"],
        cwd=str(root),
        env={"MCP_TRANSPORT": "stdio"},
    )
    output = root / ".local/verification"
    output.mkdir(parents=True, exist_ok=True)
    path = output / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
    try:
        async with Client(transport, timeout=60) as client:
            tools = [t.name for t in await client.list_tools()]
            transcript["tools"] = tools
            if len(tools) != 6:
                raise RuntimeError("Expected six tools")

            async def call(name, args):
                started = time.monotonic()
                result = await client.call_tool(name, args)
                data = result.data
                transcript["steps"].append(
                    {
                        "tool": name,
                        "arguments": args,
                        "result": data,
                        "seconds": round(time.monotonic() - started, 3),
                    }
                )
                if not isinstance(data, dict) or "error" in data:
                    raise RuntimeError(f"Tool failed: {name}")
                print(f"PASS {name}")
                return data

            await call(
                "suggest_search_filters", {"kind": "organizations", "query": "census"}
            )
            await call(
                "suggest_search_filters", {"kind": "locations", "query": "Maryland"}
            )
            first = await call(
                "find_data_for_question",
                {"request": {"query": "population", "limit": 2}},
            )
            if not first["datasets"]:
                raise RuntimeError("Expected population search results")
            record_id = first["datasets"][0]["harvest_record_id"]
            await call("inspect_dataset", {"harvest_record_id": record_id})
            if first["next_cursor"]:
                await call(
                    "find_data_for_question",
                    {
                        "request": {
                            "query": "population",
                            "limit": 2,
                            "cursor": first["next_cursor"],
                        }
                    },
                )
            await call(
                "find_data_for_question",
                {"request": {"query": "water quality", "limit": 2}},
            )
            unsupported = await call(
                "assess_comparison",
                {"request": {"metric_ids": ["population", "ad_spend"]}},
            )
            if unsupported["status"] != "unsupported":
                raise RuntimeError("Unsupported measure was accepted")
            readiness = await call("assess_comparison", {"request": {}})
            transcript["warehouse_status"] = readiness["status"]
            transcript["status"] = "PASS discovery; warehouse " + readiness["status"]
    except Exception as exc:
        transcript["status"] = "FAIL"
        transcript["error_type"] = type(exc).__name__
        raise
    finally:
        path.write_text(json.dumps(transcript, indent=2) + "\n")
        print(f"Transcript: {path.relative_to(root)}")


if __name__ == "__main__":
    asyncio.run(main())
