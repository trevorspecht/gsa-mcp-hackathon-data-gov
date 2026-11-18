"""Operator-run immutable snapshot load; runtime tools cannot invoke this module."""

import argparse
import hashlib
import json

from datagov_mcp.config import Settings
from datagov_mcp.errors import ServiceError
from datagov_mcp.registry import Registry
from datagov_mcp.snapshot import Observation
from datagov_mcp.warehouse import Warehouse


def load_snapshot(settings, execute=False):
    registry = Registry(settings)
    manifest, blocker = registry.manifest()
    if blocker:
        raise ValueError(blocker)
    content = settings.analytics_manifest.with_name("indicators.json").read_bytes()
    if hashlib.sha256(content).hexdigest() != manifest["data_sha256"]:
        raise ValueError("Prepared data hash does not match manifest")
    rows = [Observation.model_validate(r).model_dump() for r in json.loads(content)]
    if len(rows) != manifest["row_count"] or len(rows) != 72:
        raise ValueError("Expected exactly 72 county/year observations")
    keys = {(r["county_fips"], r["year"]) for r in rows}
    expected = {(c, y) for c in manifest["county_fips"] for y in manifest["years"]}
    if keys != expected or any(
        r["snapshot_id"] != manifest["snapshot_id"] for r in rows
    ):
        raise ValueError("Snapshot row grain or identity mismatch")
    table = settings.table_name
    if not execute:
        return {
            "mode": "preview",
            "table": table,
            "rows": len(rows),
            "snapshot_id": manifest["snapshot_id"],
            "actions": [
                "CREATE TABLE IF NOT EXISTS",
                "INSERT immutable snapshot",
                "verify row count",
            ],
        }
    warehouse = Warehouse(settings)
    warehouse.execute(
        f"CREATE TABLE IF NOT EXISTS {table} ("
        "county_fips STRING, county_name STRING, state_fips STRING, year INT, "
        "population BIGINT, unemployment_rate DOUBLE, snapshot_id STRING) USING DELTA",
        {},
    )
    # table comes only from validated Settings; values remain bound parameters.
    count_sql = f"SELECT COUNT(*) AS n FROM {table} WHERE snapshot_id = :snapshot"  # nosec B608
    params = {"snapshot": manifest["snapshot_id"]}
    existing = warehouse.execute(count_sql, params)["rows"]
    if int(existing[0]["n"]) != 0:
        raise ValueError(
            "Snapshot already exists; inspect it instead of appending duplicates"
        )
    fields = [
        "county_fips",
        "county_name",
        "state_fips",
        "year",
        "population",
        "unemployment_rate",
        "snapshot_id",
    ]
    values, parameters = [], {}
    for index, row in enumerate(rows):
        names = [f"r{index}_{field}" for field in fields]
        values.append("(" + ", ".join(":" + name for name in names) + ")")
        parameters.update(
            {name: row[field] for name, field in zip(names, fields, strict=True)}
        )
    # Identifiers are operator-validated; placeholders are generated, never data.
    statement = f"INSERT INTO {table} ({', '.join(fields)}) VALUES " + ", ".join(values)  # nosec B608
    warehouse.execute(statement, parameters)
    count = warehouse.execute(count_sql, params)["rows"]
    if int(count[0]["n"]) != len(rows):
        raise ValueError(
            "Loaded row count failed verification; inspect warehouse before retry"
        )
    manifest["loaded_table"] = table
    settings.analytics_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    return {"mode": "loaded", "rows": len(rows), "snapshot_id": manifest["snapshot_id"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute", action="store_true", help="Create/load the configured table"
    )
    args = parser.parse_args()
    try:
        print(json.dumps(load_snapshot(Settings(), args.execute), indent=2))
    except (ValueError, OSError, ServiceError) as exc:
        raise SystemExit(
            f"Load failed: {type(exc).__name__}; check config and query history"
        ) from None
