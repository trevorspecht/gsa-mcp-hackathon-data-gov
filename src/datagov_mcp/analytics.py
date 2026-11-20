"""Approved analytic dispatch; no tool accepts SQL, table names or URLs."""

import asyncio
import math

from datagov_mcp.errors import ServiceError
from datagov_mcp.models import CompareRequest
from datagov_mcp.registry import Registry, asset

NUMERIC = (
    "population_start",
    "population_end",
    "population_change",
    "unemployment_start",
    "unemployment_end",
    "unemployment_change",
)


def shape_rows(rows, request, expected_counties):
    by_county = {}
    for row in rows:
        county = row.get("county_fips")
        if county not in expected_counties or county in by_county:
            raise ServiceError(
                "INVALID_GRAIN",
                "Unexpected or duplicate county rows",
                "Revalidate the curated table's county/year uniqueness",
            )
        result = {"county_fips": county, "county_name": row.get("county_name")}
        for key in NUMERIC:
            value = row.get(key)
            try:
                result[key] = float(value) if value is not None else None
            except (TypeError, ValueError) as exc:
                raise ServiceError(
                    "INVALID_VALUE",
                    "Non-numeric warehouse measure",
                    "Revalidate the curated snapshot",
                ) from exc
            if result[key] is not None and not math.isfinite(result[key]):
                raise ServiceError(
                    "INVALID_VALUE",
                    "Non-finite warehouse measure",
                    "Revalidate the curated snapshot",
                )
        by_county[county] = result
    selected = set(request.county_fips or expected_counties)
    missing = sorted(
        c
        for c in selected
        if c not in by_county or any(by_county[c][key] is None for key in NUMERIC)
    )
    complete = [by_county[c] for c in sorted(selected) if c not in missing]
    filtered = [r for r in complete if matches(r, request)]
    reverse = request.sort_by != "county"
    key = "county_fips" if request.sort_by == "county" else request.sort_by
    filtered.sort(key=lambda row: (row[key], row["county_fips"]), reverse=reverse)
    return {
        "summary": summarize(complete),
        "rows": filtered[: request.limit],
        "matched_count": len(filtered),
        "truncated": len(filtered) > request.limit,
        "missing_counties": missing,
        "complete_counties": len(complete),
        "requested_counties": len(selected),
    }


def direction(value, labels):
    # Rounding absorbs float noise such as 3.3 - 3.1 = 0.19999...
    value = round(value, 6)
    return labels[0] if value > 0 else labels[1] if value < 0 else labels[2]


def summarize(complete):
    """Counts over all complete requested counties, before direction filters."""
    population = ("increased", "decreased", "unchanged")
    unemployment = ("rose", "fell", "unchanged")
    counts = {
        "counties_compared": len(complete),
        "population": dict.fromkeys(population, 0),
        "unemployment_rate": dict.fromkeys(unemployment, 0),
        "population_by_unemployment": {
            p: dict.fromkeys(unemployment, 0) for p in population
        },
    }
    for row in complete:
        pop = direction(row["population_change"], population)
        rate = direction(row["unemployment_change"], unemployment)
        counts["population"][pop] += 1
        counts["unemployment_rate"][rate] += 1
        counts["population_by_unemployment"][pop][rate] += 1
    counts["note"] = (
        "Counts cover every complete requested county and ignore direction "
        "filters, sorting and limit; quote these instead of counting rows."
    )
    return counts


def matches(row, request):
    for field, direction in (
        ("population_change", request.population_direction),
        ("unemployment_change", request.unemployment_direction),
    ):
        if direction == "increase" and row[field] <= 0:
            return False
        if direction == "decrease" and row[field] >= 0:
            return False
    return True


class Analytics:
    def __init__(self, registry: Registry, warehouse, evidence):
        self.registry, self.warehouse, self.evidence = registry, warehouse, evidence
        self.semaphore = asyncio.Semaphore(2)

    async def compare(self, request: CompareRequest):
        assessment = self.registry.assess(request)
        if not assessment["ready_to_execute"]:
            return assessment
        manifest, _ = self.registry.manifest()
        sql = asset("compare.sql").format(table=self.registry.settings.table_name)
        parameters = {
            "state": request.state_fips,
            "start_year": request.start_year,
            "end_year": request.end_year,
            "snapshot": manifest["snapshot_id"],
        }
        async with self.semaphore:
            result = await asyncio.to_thread(self.warehouse.execute, sql, parameters)
        shaped = shape_rows(result["rows"], request, manifest["county_fips"])
        evidence_id = self.evidence.save(
            {
                "request": request.model_dump(),
                "sql": sql,
                "parameters": parameters,
                "query_id": result["query_id"],
                "snapshot": manifest,
                "registry_version": self.registry.data["version"],
                "metrics": self.registry.data["metrics"],
                "result": shaped,
                "caveats": self.registry.data["join"]["caveats"],
            }
        )
        return {
            "status": "complete",
            **shaped,
            "evidence_id": evidence_id,
            "query_id": result["query_id"],
            "snapshot_id": manifest["snapshot_id"],
            "sources": self.registry.sources(manifest),
            "units": {
                "population_change": "percent",
                "unemployment_change": "percentage points",
            },
            "caveats": self.registry.data["join"]["caveats"],
        }
