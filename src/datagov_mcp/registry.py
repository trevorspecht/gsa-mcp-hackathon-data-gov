"""Reviewed semantics are separate from live discovery and execution readiness."""

import json
from importlib.resources import files
from pathlib import Path

from datagov_mcp.config import Settings
from datagov_mcp.models import CompareRequest
from datagov_mcp.snapshot import Manifest


def asset(name: str):
    packaged = files("datagov_mcp").joinpath("data", name)
    if packaged.is_file():
        return packaged.read_text()
    folder = "sql" if name.endswith(".sql") else "registry"
    return (Path(__file__).resolve().parents[2] / folder / name).read_text()


class Registry:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.data = json.loads(asset("metrics.json"))

    def suggestions(self, query: str):
        return [
            {
                "metric_id": m["id"],
                "search_terms": m["search_terms"],
                "organization_hint": m["organization_slug"],
                "note": "Suggestion only; resolve organization slug before filtering",
            }
            for m in self.data["metrics"]
            if any(term in query.casefold() for term in m["synonyms"])
        ]

    def manifest(self):
        path = self.settings.analytics_manifest
        if not path.exists():
            return None, "Verified analytic snapshot has not been prepared"
        try:
            if path.stat().st_size > 32_000:
                raise ValueError("Manifest exceeds size limit")
            data = Manifest.model_validate_json(path.read_text()).model_dump()
            if data["domain_reviewed"] is not True:
                return None, "Snapshot domain review has not been confirmed"
            if data["state_fips"] != self.data["state_fips"]:
                raise ValueError("Unsupported snapshot state")
            if not isinstance(data["years"], list) or not all(
                isinstance(y, int) for y in data["years"]
            ):
                raise ValueError("Invalid years")
            return data, None
        except (OSError, ValueError, TypeError):
            return None, "Snapshot manifest is invalid or unreadable"

    def capabilities(self):
        manifest, blocker = self.manifest()
        loaded = bool(
            manifest and manifest.get("loaded_table") == self.settings.table_name
        )
        return {
            "registry": self.data,
            "analytic_snapshot": manifest,
            "setup_blockers": ([blocker] if blocker else [])
            + self.settings.missing_warehouse_settings
            + (
                []
                if loaded
                else ["Snapshot is not verified loaded in the configured table"]
            ),
            "discovery": "Live catalog metadata search across topics",
            "execution": "Registered Maryland population/unemployment comparison only",
        }

    def assess(self, request: CompareRequest):
        reasons = []
        if set(request.metric_ids) != {m["id"] for m in self.data["metrics"]}:
            reasons.append(
                "These metrics do not have an approved comparison implementation"
            )
        if request.state_fips != self.data["state_fips"]:
            reasons.append(
                "Only Maryland county/county-equivalent geography is supported"
            )
        if not {request.start_year, request.end_year} <= set(self.data["years"]):
            reasons.append("Selected years are outside the planned 2022–2024 coverage")
        manifest, blocker = self.manifest()
        if manifest:
            if not {request.start_year, request.end_year} <= set(manifest["years"]):
                reasons.append("Selected years are absent from the verified snapshot")
            if not set(request.county_fips) <= set(manifest["county_fips"]):
                reasons.append(
                    "Selected counties are absent from the verified snapshot"
                )
        setup = (
            [blocker] if blocker else []
        ) + self.settings.missing_warehouse_settings
        if manifest and manifest.get("loaded_table") != self.settings.table_name:
            setup.append("Snapshot is not verified loaded in the configured table")
        return {
            "compatible": not reasons,
            "ready_to_execute": not reasons and not setup,
            "status": "unsupported"
            if reasons
            else "setup_required"
            if setup
            else "ready",
            "incompatibilities": reasons,
            "setup_blockers": setup,
            "comparison": request.model_dump(),
            "metrics": self.data["metrics"],
            "join": self.data["join"],
            "sources": self.data["sources"],
            "snapshot_id": manifest["snapshot_id"] if manifest else None,
            "note": "Registered semantic compatibility and readiness are separate",
        }
