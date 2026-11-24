"""Reviewed dataset registry and generic connectors.

Dataset-specific facts live in registry/datasets.json. Tools address datasets and
measures by registry ID; SQL text, table names and URLs are never tool inputs.
"""

import asyncio
import csv
import hashlib
import io
import json
import math
import re
from datetime import datetime, timezone

import httpx

from datagov_mcp.errors import ServiceError
from datagov_mcp.models import ObservationRequest
from datagov_mcp.registry import Registry, asset
from datagov_mcp.tls import verified_context

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
MAX_ROWS = 500


def packaged_snapshot():
    data = json.loads(asset("science.json"))
    identity = data.pop("snapshot_id")
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    if not data.get("domain_reviewed") or digest[:24] != identity:
        raise ServiceError(
            "INVALID_SNAPSHOT",
            "Packaged snapshot integrity check failed",
            "Rebuild the reviewed asset",
        )
    return {**data, "snapshot_id": identity}


def parse_noaa_annual(raw, expected_units):
    """NOAA Climate at a Glance annual CSV: '# Units' header, Date=YYYY12 rows."""
    content = raw.decode("utf-8-sig")
    if f"# Units: {expected_units}" not in content:
        raise ValueError("Unexpected units")
    reader = csv.DictReader(
        io.StringIO(
            "\n".join(line for line in content.splitlines() if not line.startswith("#"))
        )
    )
    if reader.fieldnames != ["Date", "Value"]:
        raise ValueError("Unexpected columns")
    rows, seen = [], set()
    for row in reader:
        year = int(row["Date"][:4])
        value = float(row["Value"])
        if row["Date"] != f"{year}12" or year in seen:
            raise ValueError("Expected unique calendar-year rows")
        if not math.isfinite(value) or value <= -90:
            raise ValueError("Missing or invalid value")
        seen.add(year)
        rows.append({"period": year, "value": value})
    if not rows:
        raise ValueError("No observations")
    return rows


PARSERS = {"noaa_climate_at_a_glance_annual": parse_noaa_annual}


class Datasets:
    def __init__(self, settings, warehouse, evidence, transport=None):
        self.settings = settings
        self.warehouse = warehouse
        self.evidence = evidence
        self.transport = transport
        self.county = Registry(settings)
        self.data = json.loads(asset("datasets.json"))
        self.by_id = {d["id"]: d for d in self.data["datasets"]}
        for dataset in self.data["datasets"]:
            for measure in dataset["measures"]:
                if measure.get("column") and not IDENTIFIER.match(measure["column"]):
                    raise ValueError("Registry column must be a plain identifier")
            connector = dataset["connector"]
            for key in ("key_column", "name_column", "period_column"):
                if key in connector and not IDENTIFIER.match(connector[key]):
                    raise ValueError("Registry column must be a plain identifier")
            for column in connector.get("fixed_filters", {}):
                if not IDENTIFIER.match(column):
                    raise ValueError("Registry column must be a plain identifier")
        self.semaphore = asyncio.Semaphore(2)

    def get(self, dataset_id):
        dataset = self.by_id.get(dataset_id)
        if not dataset:
            raise ServiceError(
                "UNKNOWN_DATASET",
                "Dataset is not in the reviewed registry",
                "Call list_queryable_datasets for available IDs",
            )
        return dataset

    def measures(self, dataset, measure_ids):
        known = {m["id"]: m for m in dataset["measures"]}
        selected = measure_ids or list(known)
        unknown = [m for m in selected if m not in known]
        if unknown:
            raise ServiceError(
                "UNKNOWN_MEASURE",
                "Measure is not registered for this dataset",
                "Use measure IDs from list_queryable_datasets",
            )
        return [known[m] for m in dict.fromkeys(selected)]

    def readiness(self, dataset):
        connector = dataset["connector"]
        if connector["type"] == "warehouse":
            manifest, blocker = self.county.manifest()
            blockers = ([blocker] if blocker else []) + (
                self.settings.missing_warehouse_settings
            )
            if manifest and manifest.get("loaded_table") != self.settings.table_name:
                blockers.append(
                    "Snapshot is not verified loaded in the configured table"
                )
            if not manifest:
                return {"ready": False, "blockers": blockers}
            return {
                "ready": not blockers,
                "blockers": blockers,
                "periods": manifest["years"],
                "geography_ids": manifest["county_fips"],
                "snapshot_id": manifest["snapshot_id"],
                "sources": self.county.sources(manifest),
                "storage": "Reviewed warehouse snapshot",
            }
        series = self.series(dataset)
        return {
            "ready": True,
            "blockers": [],
            "periods": [r["year"] for r in series["observations"]],
            "geography_ids": [dataset["geography"]["single"]["id"]],
            "snapshot_id": packaged_snapshot()["snapshot_id"],
            "sources": [series["source"]],
            "storage": "Reviewed packaged snapshot"
            + ("; live publisher refresh available" if connector.get("live") else ""),
        }

    def series(self, dataset):
        name = dataset["connector"]["series"]
        return next(d for d in packaged_snapshot()["datasets"] if d["id"] == name)

    def describe(self, dataset):
        state = self.readiness(dataset)
        return {
            "dataset_id": dataset["id"],
            "title": dataset["title"],
            "publisher": dataset["publisher"],
            "description": dataset["description"],
            "geography": {
                k: v for k, v in dataset["geography"].items() if k != "single"
            },
            "measures": [
                {k: v for k, v in m.items() if k not in ("column", "source_id")}
                for m in dataset["measures"]
            ],
            "periods": state.get("periods", []),
            "ready": state["ready"],
            "setup_blockers": state["blockers"],
            "storage": state.get("storage"),
            "live_refresh": bool(dataset["connector"].get("live")),
            "sources": state.get("sources", dataset.get("sources", [])),
            "catalog_identifiers": dataset.get("catalog_identifiers", []),
            "caveats": dataset.get("caveats", []) + self._series_caveats(dataset),
        }

    def _series_caveats(self, dataset):
        if dataset["connector"]["type"] != "packaged_snapshot":
            return []
        return self.series(dataset).get("caveats", [])

    def catalog_scopes(self, identifier):
        return [
            self.describe(d)
            for d in self.data["datasets"]
            if identifier and identifier in d.get("catalog_identifiers", [])
        ]

    def search_terms(self, question):
        lowered = question.casefold()
        return [
            {
                "dataset_id": d["id"],
                "matched_keywords": [k for k in d["keywords"] if k in lowered],
                "note": "Registry suggestion only; does not change search parameters",
            }
            for d in self.data["datasets"]
            if any(k in lowered for k in d["keywords"])
        ]

    async def observations(self, request, live=False):
        dataset = self.get(request.dataset_id)
        measures = self.measures(dataset, request.measure_ids)
        state = self.readiness(dataset)
        if not state["ready"]:
            return {
                "status": "setup_required",
                "dataset_id": dataset["id"],
                "setup_blockers": state["blockers"],
            }
        periods = [
            p
            for p in state["periods"]
            if (request.start_period is None or p >= request.start_period)
            and (request.end_period is None or p <= request.end_period)
        ]
        if request.geography_ids and not set(request.geography_ids) <= set(
            state["geography_ids"]
        ):
            return {
                "status": "unsupported",
                "dataset_id": dataset["id"],
                "reason": "Requested geography is outside this dataset's coverage",
                "available_geography_ids": state["geography_ids"],
                "geography": dataset["geography"],
            }
        if not periods:
            return {
                "status": "unsupported",
                "dataset_id": dataset["id"],
                "reason": "No observations in the requested period",
                "available_periods": state["periods"],
            }
        connector = dataset["connector"]
        provenance = {"storage": state["storage"], "snapshot_id": state["snapshot_id"]}
        if connector["type"] == "warehouse":
            rows, query = await self._warehouse_rows(
                dataset, measures, periods, request.geography_ids
            )
            provenance.update(query)
        elif live and connector.get("live"):
            rows, fetched = await self._live_rows(dataset, measures, periods)
            provenance = fetched
        else:
            series = self.series(dataset)
            single = dataset["geography"]["single"]
            rows = [
                {
                    "geography_id": single["id"],
                    "geography_name": single["name"],
                    "period": r["year"],
                    measures[0]["id"]: r["value"],
                }
                for r in series["observations"]
                if r["year"] in periods
            ]
        result = {
            "status": "complete",
            "dataset_id": dataset["id"],
            "title": dataset["title"],
            "geography": {
                k: v for k, v in dataset["geography"].items() if k != "single"
            },
            "measures": [
                {k: m[k] for k in ("id", "label", "unit", "observation")}
                for m in measures
            ],
            "rows": rows,
            "row_count": len(rows),
            "available_periods": state["periods"],
            "missing_periods": [
                p for p in periods if p not in {r["period"] for r in rows}
            ],
            "sources": provenance.pop("sources", None) or state["sources"],
            "provenance": provenance,
            "caveats": dataset.get("caveats", []) + self._series_caveats(dataset),
        }
        evidence_id = self.evidence.save(
            {"request": request.model_dump(), "result": result}
        )
        return {**result, "evidence_id": evidence_id}

    async def _warehouse_rows(self, dataset, measures, periods, geography_ids):
        connector = dataset["connector"]
        key, name, period = (
            connector["key_column"],
            connector["name_column"],
            connector["period_column"],
        )
        columns = ", ".join([key, name, period] + [m["column"] for m in measures])
        filters, parameters = [], {}
        for index, (column, value) in enumerate(connector["fixed_filters"].items()):
            filters.append(f"{column} = :fixed{index}")
            parameters[f"fixed{index}"] = value
        manifest, _ = self.county.manifest()
        filters.append("snapshot_id = :snapshot")
        parameters["snapshot"] = manifest["snapshot_id"]
        filters.append(f"{period} >= :start_period AND {period} <= :end_period")
        parameters.update(start_period=min(periods), end_period=max(periods))
        if geography_ids:
            names = [f"g{i}" for i in range(len(geography_ids))]
            filters.append(f"{key} IN (" + ", ".join(":" + n for n in names) + ")")
            parameters.update(dict(zip(names, geography_ids, strict=True)))
        # Identifiers come only from the validated registry and operator settings;
        # every request value is a bound parameter.
        sql = (
            f"SELECT {columns} FROM {self.settings.table_name} "  # nosec B608
            f"WHERE {' AND '.join(filters)} ORDER BY {key}, {period} LIMIT {MAX_ROWS}"
        )
        async with self.semaphore:
            result = await asyncio.to_thread(self.warehouse.execute, sql, parameters)
        rows, seen = [], set()
        for raw in result["rows"]:
            identity = (raw[key], int(raw[period]))
            if identity in seen:
                raise ServiceError(
                    "INVALID_GRAIN",
                    "Duplicate geography/period rows",
                    "Revalidate the curated table's uniqueness",
                )
            seen.add(identity)
            row = {
                "geography_id": raw[key],
                "geography_name": raw[name],
                "period": int(raw[period]),
            }
            for measure in measures:
                value = raw.get(measure["column"])
                row[measure["id"]] = None if value is None else _number(value)
            rows.append(row)
        return rows, {
            "sql": sql,
            "parameters": parameters,
            "query_id": result["query_id"],
        }

    async def _live_rows(self, dataset, measures, periods):
        live = dataset["connector"]["live"]
        async with asyncio.timeout(live["timeout_seconds"]):
            async with httpx.AsyncClient(
                base_url=live["origin"],
                timeout=live["timeout_seconds"],
                follow_redirects=False,
                trust_env=False,
                verify=verified_context(),
                transport=self.transport,
            ) as client:
                async with client.stream("GET", live["path"]) as response:
                    if response.status_code != 200:
                        raise ServiceError(
                            "UPSTREAM_ERROR",
                            "Publisher request failed",
                            "Retry later or use the reviewed snapshot",
                        )
                    raw = bytearray()
                    async for chunk in response.aiter_bytes():
                        raw.extend(chunk)
                        if len(raw) > live["max_bytes"]:
                            raise ServiceError(
                                "UPSTREAM_TOO_LARGE",
                                "Publisher file exceeds the reviewed size budget",
                                "Use the reviewed snapshot",
                            )
        try:
            parsed = PARSERS[live["parser"]](bytes(raw), live["units"])
        except (ValueError, UnicodeError) as exc:
            raise ServiceError(
                "UPSTREAM_INVALID",
                "Publisher file failed validation",
                "Use the reviewed snapshot; the publisher format may have changed",
            ) from exc
        single = dataset["geography"]["single"]
        rows = [
            {
                "geography_id": single["id"],
                "geography_name": single["name"],
                "period": r["period"],
                measures[0]["id"]: r["value"],
            }
            for r in parsed
            if r["period"] in periods
        ]
        url = live["origin"] + live["path"]
        return rows, {
            "storage": "Live publisher file",
            "sources": [
                {
                    **self.series(dataset)["source"],
                    "url": url,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            ],
            "url": url,
            "bytes": len(raw),
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

    async def change(self, request):
        dataset = self.get(request.dataset_id)
        measures = self.measures(dataset, request.measure_ids)
        observed = await self.observations(
            ObservationRequest(
                dataset_id=request.dataset_id,
                measure_ids=[m["id"] for m in measures],
                geography_ids=request.geography_ids,
                start_period=request.start_period,
                end_period=request.end_period,
            )
        )
        if observed["status"] != "complete":
            return observed
        by_key = {(r["geography_id"], r["period"]): r for r in observed["rows"]}
        geographies = sorted({r["geography_id"] for r in observed["rows"]})
        names = {r["geography_id"]: r["geography_name"] for r in observed["rows"]}
        if (request.start_period not in observed["available_periods"]) or (
            request.end_period not in observed["available_periods"]
        ):
            return {
                "status": "unsupported",
                "dataset_id": dataset["id"],
                "reason": "Start and end periods must both be observed",
                "available_periods": observed["available_periods"],
            }
        complete, missing = [], []
        for geography in request.geography_ids or geographies:
            start = by_key.get((geography, request.start_period))
            end = by_key.get((geography, request.end_period))
            if (
                not start
                or not end
                or any(start[m["id"]] is None or end[m["id"]] is None for m in measures)
            ):
                missing.append(geography)
                continue
            row = {"geography_id": geography, "geography_name": names.get(geography)}
            for measure in measures:
                a, b = start[measure["id"]], end[measure["id"]]
                if measure["change"] == "percent":
                    value = None if a == 0 else 100.0 * (b - a) / a
                else:
                    value = b - a
                row.update(
                    {
                        f"{measure['id']}_start": a,
                        f"{measure['id']}_end": b,
                        f"{measure['id']}_change": value,
                    }
                )
            complete.append(row)
        summary = {
            "geographies_compared": len(complete),
            "directions": {
                m["id"]: _directions(complete, m["id"] + "_change") for m in measures
            },
        }
        if len(measures) == 2:
            first, second = (m["id"] + "_change" for m in measures)
            summary["joint_directions"] = {
                a: {
                    b: sum(
                        1
                        for r in complete
                        if _direction(r[first]) == a and _direction(r[second]) == b
                    )
                    for b in ("increased", "decreased", "unchanged")
                }
                for a in ("increased", "decreased", "unchanged")
            }
        summary["note"] = (
            "Counts cover every complete requested geography before filters, "
            "sorting and limit; quote these instead of counting rows."
        )
        filtered = [r for r in complete if _matches(r, request.direction_filters)]
        if request.sort_by:
            if request.sort_by not in {m["id"] for m in measures}:
                raise ServiceError(
                    "INVALID_SORT",
                    "sort_by must be one of the selected measures",
                    "Use a selected measure ID",
                )
            field = request.sort_by + "_change"
            filtered.sort(key=lambda r: (r[field], r["geography_id"]), reverse=True)
        result = {
            "status": "complete",
            "dataset_id": dataset["id"],
            "title": dataset["title"],
            "geography": public_geography(dataset),
            "start_period": request.start_period,
            "end_period": request.end_period,
            "measures": [
                {
                    "id": m["id"],
                    "label": m["label"],
                    "unit": m["unit"],
                    "change_definition": "100 × (end − start) / start"
                    if m["change"] == "percent"
                    else "end − start",
                    "change_unit": m["change_unit"],
                }
                for m in measures
            ],
            "summary": summary,
            "rows": filtered[: request.limit],
            "matched_count": len(filtered),
            "truncated": len(filtered) > request.limit,
            "missing_geographies": missing,
            "sources": observed["sources"],
            "source_evidence_id": observed["evidence_id"],
            "caveats": observed["caveats"]
            + [
                "Change between two endpoints is not a trend estimate or causal effect."
            ],
        }
        evidence_id = self.evidence.save(
            {
                "request": request.model_dump(),
                "result": result,
                "observation_provenance": observed["provenance"],
            }
        )
        return {**result, "evidence_id": evidence_id}

    def compatibility(self, request):
        selections = []
        for item in request.datasets:
            dataset = self.get(item.dataset_id)
            measures = self.measures(dataset, item.measure_ids)
            state = self.readiness(dataset)
            selections.append((dataset, measures, state))
        pairs = []
        for i, (left, lm, ls) in enumerate(selections):
            for right, rm, rs in selections[i + 1 :]:
                overlap = sorted(
                    set(ls.get("periods", [])) & set(rs.get("periods", []))
                )
                same_level = left["geography"]["level"] == right["geography"]["level"]
                same_area = left["geography"]["area"] == right["geography"]["area"]
                shared = sorted(
                    set(ls.get("geography_ids", [])) & set(rs.get("geography_ids", []))
                )
                reasons = []
                if not (same_level and same_area and shared):
                    reasons.append(
                        f"Geography differs: {left['geography']['level']} of "
                        f"{left['geography']['area']} vs "
                        f"{right['geography']['level']} of {right['geography']['area']}"
                    )
                if len(overlap) < 3:
                    reasons.append(
                        f"Only {len(overlap)} overlapping period(s); at least 3 needed"
                    )
                if not (ls["ready"] and rs["ready"]):
                    reasons.append("A dataset requires setup before retrieval")
                pairs.append(
                    {
                        "datasets": [left["id"], right["id"]],
                        "measures": [[m["id"] for m in lm], [m["id"] for m in rm]],
                        "units": [[m["unit"] for m in lm], [m["unit"] for m in rm]],
                        "overlapping_periods": overlap,
                        "shared_geography_ids": shared[:50],
                        "status": "descriptive_alignment_possible"
                        if not reasons
                        else "not_comparable",
                        "reasons": reasons
                        or [
                            "Same geography and ≥3 shared periods allow side-by-side "
                            "description; not statistical or causal validation"
                        ],
                    }
                )
        return {
            "pairs": pairs,
            "limitations": [
                "No correlation coefficients, interpolation or causal joins computed",
                "Autocorrelation, trends and confounders need an analysis design",
            ],
            "next_steps": [
                "Preview each dataset's observations, units and missing periods",
                "Search the catalog for sources sharing geography and periods",
            ],
        }


def public_geography(dataset):
    return {k: v for k, v in dataset["geography"].items() if k != "single"}


def _number(value):
    number = float(value)
    if not math.isfinite(number):
        raise ServiceError(
            "INVALID_VALUE", "Non-finite measure", "Revalidate the curated snapshot"
        )
    return int(number) if number.is_integer() and "." not in str(value) else number


def _direction(value):
    value = round(value, 6)
    return "increased" if value > 0 else "decreased" if value < 0 else "unchanged"


def _directions(rows, field):
    counts = dict.fromkeys(("increased", "decreased", "unchanged"), 0)
    for row in rows:
        counts[_direction(row[field])] += 1
    return counts


def _matches(row, filters):
    for measure, direction in filters.items():
        value = round(row[measure + "_change"], 6)
        if direction == "increase" and value <= 0:
            return False
        if direction == "decrease" and value >= 0:
            return False
    return True
