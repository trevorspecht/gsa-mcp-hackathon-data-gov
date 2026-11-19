"""Read-only queries over fixed, reviewed climate and agricultural-practice data."""

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from datagov_mcp.errors import ServiceError
from datagov_mcp.registry import asset
from datagov_mcp.tools.common import guarded

Dataset = Literal[
    "md_temperature",
    "md_precipitation",
    "chesapeake_cover_crops",
    "chesapeake_conservation_tillage",
]


class ScienceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset_id: Dataset
    start_year: int = Field(default=1985, ge=1985, le=2012)
    end_year: int = Field(default=2012, ge=1985, le=2012)

    @model_validator(mode="after")
    def years(self):
        if self.end_year < self.start_year:
            raise ValueError("end_year must be at least start_year")
        return self


def snapshot():
    data = json.loads(asset("science.json"))
    identity = data.pop("snapshot_id")
    if (
        not data.get("domain_reviewed")
        or hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:24]
        != identity
    ):
        raise ServiceError(
            "INVALID_SNAPSHOT",
            "Science asset integrity check failed",
            "Rebuild reviewed asset",
        )
    return {**data, "snapshot_id": identity}


def query(request, evidence):
    data = snapshot()
    dataset = next(d for d in data["datasets"] if d["id"] == request.dataset_id)
    rows = [
        r
        for r in dataset["observations"]
        if request.start_year <= r["year"] <= request.end_year
    ]
    if not rows:
        return {
            "status": "unsupported",
            "reason": "No observations in requested interval",
            "available_years": [r["year"] for r in dataset["observations"]],
        }
    result = {
        "status": "complete",
        "dataset_id": dataset["id"],
        "title": dataset["title"],
        "geography": dataset["geography"],
        "unit": dataset["unit"],
        "rows": rows,
        "source": dataset["source"],
        "method": dataset["method"],
        "snapshot_id": data["snapshot_id"],
        "caveats": dataset["caveats"],
        "available_years": [r["year"] for r in dataset["observations"]],
        "summary": {
            "observations": len(rows),
            "first_year": rows[0]["year"],
            "last_year": rows[-1]["year"],
            "first_value": rows[0]["value"],
            "last_value": rows[-1]["value"],
            "endpoint_difference": round(rows[-1]["value"] - rows[0]["value"], 4),
            "note": (
                "Difference uses first/last available observations, not an "
                "inferred trend or causal effect."
            ),
        },
    }
    identifier = evidence.save(
        {
            "request": request.model_dump(),
            "result": result,
            "snapshot_id": data["snapshot_id"],
            "source": dataset["source"],
        }
    )
    return {**result, "evidence_id": identifier}


def register(mcp, services):
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    @guarded
    def inspect_science_capabilities() -> dict:
        """List verified historical climate/agriculture query scopes, years and sources.

        Maryland annual temperature/precipitation (1985–2012), Chesapeake watershed
        cover crops (2002/2012), tillage (1985/1992/2002/2012). Different geographies:
        never join these or infer climate caused practice adoption. Discovery remains
        available for other datasets. Inspect before query_science_series.
        """
        data = snapshot()
        return {
            "snapshot_id": data["snapshot_id"],
            "datasets": [
                {k: v for k, v in d.items() if k != "observations"}
                | {"available_years": [r["year"] for r in d["observations"]]}
                for d in data["datasets"]
            ],
        }

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    @guarded
    def query_science_series(request: ScienceRequest) -> dict:
        """Query a reviewed climate or agricultural-practice series and save evidence.

        Only the fixed dataset IDs and 1985–2012 window are supported; returns all
        available observations in the interval, units, method and endpoint difference.
        Missing years stay missing. Tillage/cover crops are allocated area estimates
        in square kilometres, not acres or adoption rates. Use get_analysis_evidence
        to reproduce; no arbitrary source URLs, SQL, joins or causal analysis.
        """
        return query(request, services.evidence)
