"""User-approved previews through fixed reviewed routes, not catalog URLs."""

import asyncio
import csv
import hashlib
import io
from datetime import datetime, timezone
from itertools import combinations

import httpx
from pydantic import BaseModel, ConfigDict, Field

from datagov_mcp.tls import verified_context
from datagov_mcp.tools.common import guarded
from datagov_mcp.tools.science import Dataset, ScienceRequest, query, snapshot

MAX_BYTES = 100_000
NOAA_ORIGIN = "https://www.ncei.noaa.gov"


class ExploreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset_ids: list[Dataset] = Field(min_length=1, max_length=4)


def choices():
    return [
        {
            "dataset_id": d["id"],
            "title": d["title"],
            "geography": d["geography"],
            "available_years": [r["year"] for r in d["observations"]],
            "source": d["source"],
            "unit": d["unit"],
            "retrieval": "live NOAA file"
            if d["id"].startswith("md_")
            else "reviewed USGS historical snapshot",
        }
        for d in snapshot()["datasets"]
    ]


def parse_climate(raw, dataset_id):
    content = raw.decode("utf-8-sig")
    units = "Degrees Fahrenheit" if dataset_id == "md_temperature" else "Inches"
    if f"# Units: {units}" not in content:
        raise ValueError("Unexpected units")
    reader = csv.DictReader(
        io.StringIO(
            "\n".join(line for line in content.splitlines() if not line.startswith("#"))
        )
    )
    if reader.fieldnames != ["Date", "Value"]:
        raise ValueError("Unexpected columns")
    rows = []
    for row in reader:
        year = int(row["Date"][:4])
        value = float(row["Value"])
        if row["Date"] != f"{year}12" or not -90 < value < 200:
            raise ValueError("Invalid annual observation")
        rows.append({"year": year, "value": value})
    if [r["year"] for r in rows] != list(range(1985, 2013)):
        raise ValueError("Unexpected year coverage")
    return rows


async def fetch_climate(dataset, evidence, transport=None):
    variable = "tavg" if dataset["id"] == "md_temperature" else "pcp"
    path = (
        "/access/monitoring/climate-at-a-glance/statewide/time-series/18/"
        f"{variable}/12/12/1985-2012.csv"
    )
    async with httpx.AsyncClient(
        base_url=NOAA_ORIGIN,
        timeout=20,
        follow_redirects=False,
        trust_env=False,
        verify=verified_context(),
        transport=transport,
    ) as client:
        async with client.stream("GET", path) as response:
            if response.status_code != 200:
                raise ValueError("Publisher request failed")
            raw = bytearray()
            async for chunk in response.aiter_bytes():
                raw.extend(chunk)
                if len(raw) > MAX_BYTES:
                    raise ValueError("Publisher file exceeds budget")
    rows = parse_climate(bytes(raw), dataset["id"])
    result = {
        "status": "complete",
        "dataset_id": dataset["id"],
        "title": dataset["title"],
        "unit": dataset["unit"],
        "geography": dataset["geography"],
        "rows": rows,
        "available_years": [r["year"] for r in rows],
        "source": {
            **dataset["source"],
            "url": NOAA_ORIGIN + path,
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
        "retrieval": "live publisher file",
        "bytes": len(raw),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "method": dataset["method"],
        "caveats": dataset["caveats"],
        "columns": ["year", "value"],
    }
    return {
        **result,
        "evidence_id": evidence.save(
            {
                "request": {"dataset_id": dataset["id"], "operation": "live preview"},
                "result": result,
            }
        ),
    }


def compatibility(results):
    comparisons = []
    complete = [r for r in results if r.get("status") == "complete"]
    for left, right in combinations(complete, 2):
        overlap = sorted(set(left["available_years"]) & set(right["available_years"]))
        same_geography = left["geography"] == right["geography"]
        enough = len(overlap) >= 3
        comparisons.append(
            {
                "dataset_ids": [left["dataset_id"], right["dataset_id"]],
                "overlapping_years": overlap,
                "same_geography": same_geography,
                "status": "descriptive_alignment_only"
                if same_geography and enough
                else "not_comparable",
                "reason": (
                    "Matching annual geography/years permit descriptive alignment; "
                    "not statistical validation, independent samples or causal evidence"
                )
                if same_geography and enough
                else ("Different geography or fewer than three overlapping years"),
            }
        )
    return {
        "pairs": comparisons,
        "limitations": [
            "No correlation coefficients, interpolation or causal joins computed",
            "Climate and watershed practice estimates describe different geography",
            "Autocorrelation, trends and confounders need an analysis design",
        ],
        "next_steps": [
            "Inspect the preview tables, units and missing years",
            "Find repeated climate/practice observations for matching geography",
            "Explore climate descriptively; do not infer practice adoption",
        ],
    }


async def explore(request, evidence, transport=None):
    datasets = {d["id"]: d for d in snapshot()["datasets"]}
    results = []
    for identity in dict.fromkeys(request.dataset_ids):
        try:
            async with asyncio.timeout(25):
                if identity.startswith("md_"):
                    result = await fetch_climate(
                        datasets[identity], evidence, transport
                    )
                else:
                    result = query(ScienceRequest(dataset_id=identity), evidence)
                    result["retrieval"] = (
                        "reviewed historical snapshot; not a live download"
                    )
                    result["columns"] = ["year", "value"]
                results.append(result)
        except (TimeoutError, httpx.HTTPError, ValueError, UnicodeError):
            results.append(
                {
                    "dataset_id": identity,
                    "status": "failed",
                    "reason": "Publisher unavailable or preview validation failed",
                }
            )
    return {
        "status": "complete"
        if all(r["status"] == "complete" for r in results)
        else "partial",
        "datasets": results,
        "compatibility": compatibility(results),
        "budget": "Up to 4 reviewed series; 25 seconds/source, 100 KB/live file",
        "scope": "Explicit previews; no arbitrary URLs, SQL or correlations",
    }


def register(mcp, services):
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    def list_exploration_options() -> dict:
        """List reviewed series selectable for explicit data preview.

        NOAA Maryland climate files can be fetched live within bounds. USGS practice
        data use the reviewed historical snapshot, not a new publisher download.
        Other catalog records remain unavailable without connector development.
        """
        return {
            "datasets": choices(),
            "next_steps": [
                "Select reviewed series and preview actual observations",
                "Check geography and year overlap before considering analysis",
            ],
        }

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    @guarded
    async def preview_selected_data(request: ExploreRequest) -> dict:
        """Preview explicitly selected reviewed series and assess descriptive alignment.

        Call only after the user requests actual data or approves a selection. Never
        infer permission from discovery. Fixed NOAA origin/paths, 25s and 100KB caps;
        USGS uses the historical snapshot. Failures retained per source; no arbitrary
        downloads or correlation computation. Return source hashes and evidence IDs.
        """
        return await explore(request, services.evidence)
