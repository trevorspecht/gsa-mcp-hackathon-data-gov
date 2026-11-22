"""Warehouse snapshot manifest checks, separate from live catalog discovery."""

import json
from importlib.resources import files
from pathlib import Path

from datagov_mcp.config import Settings
from datagov_mcp.snapshot import Manifest


def asset(name: str):
    packaged = files("datagov_mcp").joinpath("data", name)
    if packaged.is_file():
        return packaged.read_text()
    folder = "sql" if name.endswith(".sql") else "registry"
    return (Path(__file__).resolve().parents[2] / folder / name).read_text()


def warehouse_dataset():
    return next(
        d
        for d in json.loads(asset("datasets.json"))["datasets"]
        if d["connector"]["type"] == "warehouse"
    )


class Registry:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.dataset = warehouse_dataset()

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
            if data["state_fips"] != self.dataset["connector"]["fixed_filters"].get(
                "state_fips"
            ):
                raise ValueError("Unsupported snapshot state")
            return data, None
        except (OSError, ValueError, TypeError):
            return None, "Snapshot manifest is invalid or unreadable"

    def sources(self, manifest):
        if not manifest:
            return self.dataset["sources"]
        verified = {s["id"]: s for s in manifest["sources"]}
        return [
            {
                **source,
                **verified[source["id"]],
                "verification": (
                    "Snapshot source schema/coverage checked; domain reviewed"
                ),
                "snapshot_id": manifest["snapshot_id"],
            }
            for source in self.dataset["sources"]
        ]
