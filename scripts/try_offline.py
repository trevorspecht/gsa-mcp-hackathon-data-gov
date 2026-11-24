"""Try the MCP server without Databricks: real stdio MCP calls, no credentials.

Shows discovery against the live Data.gov catalog and queries of the reviewed
climate and agricultural-practice datasets packaged with the server. The county
dataset needs a Databricks SQL warehouse, so it reports what setup is missing.
"""

import asyncio
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

ROOT = Path(__file__).resolve().parents[1]


def show(title, lines):
    print(f"\n== {title}")
    for line in lines:
        print("  " + line)


async def main():
    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "datagov_mcp.app"],
        cwd=str(ROOT),
        env={"MCP_TRANSPORT": "stdio"},
    )
    async with Client(transport, timeout=60) as client:

        async def call(name, args=None):
            return (await client.call_tool(name, args or {})).data

        tools = [tool.name for tool in await client.list_tools()]
        show(f"{len(tools)} MCP tools", tools)

        found = await call(
            "find_data_for_question", {"request": {"query": "cover crops", "limit": 3}}
        )
        show(
            "Data.gov catalog search: 'cover crops' (live)",
            [d["title"] for d in found.get("datasets", [])]
            or [str(found.get("error", "no results"))],
        )

        registry = await call("list_queryable_datasets")
        show(
            "Registered datasets that can return observations",
            [
                f"{d['dataset_id']}: {'ready' if d['ready'] else 'needs setup'}"
                for d in registry["datasets"]
            ],
        )

        change = await call(
            "analyze_change",
            {
                "request": {
                    "dataset_id": "chesapeake_cover_crops",
                    "start_period": 2002,
                    "end_period": 2012,
                }
            },
        )
        row = change["rows"][0]
        show(
            "Cover-crop change, Chesapeake Bay watershed, 2002 to 2012",
            [
                f"{row['cover_crop_area_start']} -> {row['cover_crop_area_end']} km2 "
                f"(change {row['cover_crop_area_change']} km2)",
                change["caveats"][-1],
            ],
        )

        pairs = await call(
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
        show(
            "Can climate and cover-crop data be compared?",
            [
                f"{' + '.join(p['datasets'])}: {p['status']} ({p['reasons'][0]})"
                for p in pairs["pairs"]
            ],
        )

        county = await call(
            "query_dataset",
            {"request": {"dataset_id": "md_county_population_unemployment"}},
        )
        if county.get("status") == "complete":
            lines = [
                f"status: complete ({county['row_count']} rows from the warehouse)"
            ]
        else:
            lines = [f"status: {county.get('status')}"] + [
                f"missing: {b}" for b in county.get("setup_blockers", [])
            ]
        show("County dataset (needs a Databricks SQL warehouse)", lines)


if __name__ == "__main__":
    asyncio.run(main())
