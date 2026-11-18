"""Catalog workflow: explicit filters, bound cursors, and source inspection."""

import json
import time
from collections import OrderedDict
from uuid import UUID, uuid4

from pydantic import ValidationError

from datagov_mcp.errors import ServiceError
from datagov_mcp.http import CatalogHTTP
from datagov_mcp.metadata import card
from datagov_mcp.models import SearchEnvelope, SearchRequest


class Catalog:
    def __init__(self, http: CatalogHTTP):
        self.http = http
        self.cursors = OrderedDict()

    def api_path(self, suffix):
        prefix = "/api/" if self.http.settings.catalog_interface == "direct" else "/"
        return prefix + suffix

    def _continuation(self, request):
        signature = request.model_dump(exclude={"cursor"})
        if not request.cursor:
            return signature, None, 1
        saved = self.cursors.get(request.cursor)
        if not saved or time.monotonic() - saved[0] > 900:
            raise ServiceError(
                "CURSOR_EXPIRED",
                "Search cursor expired or unknown",
                "Restart the search; cursors are process-local",
            )
        _, original, after, page = saved
        if original != signature:
            raise ServiceError(
                "CURSOR_MISMATCH",
                "Filters changed during pagination",
                "Omit cursor to begin a new search",
            )
        return signature, after, page

    async def search(self, request: SearchRequest):
        signature, after, page = self._continuation(request)
        params = [
            ("q", request.query),
            ("sort", request.sort),
            ("per_page", str(request.limit)),
        ]
        for key, value in (
            ("org_slug", request.organization),
            ("org_type", request.organization_type),
            ("after", after),
        ):
            if value:
                params.append((key, value))
        params.extend(("keyword", value) for value in request.keywords)
        if request.location_id:
            geometry, _ = await self.http.get(
                self.api_path("location/" + request.location_id)
            )
            shape = geometry.get("geometry")
            if not isinstance(shape, dict) or not shape.get("type"):
                raise ServiceError(
                    "INVALID_RESPONSE",
                    "Location has no geometry",
                    "Select another location",
                )
            encoded = json.dumps(shape)
            if len(encoded) > 100_000:
                raise ServiceError(
                    "GEOMETRY_TOO_LARGE",
                    "Location boundary is too large",
                    "Choose a simpler geographic filter",
                )
            params.extend(
                [
                    ("spatial_geometry", encoded),
                    ("spatial_within", str(request.spatial_within).lower()),
                ]
            )
        body, meta = await self.http.get("/search", params)
        try:
            result = SearchEnvelope.model_validate(body)
        except ValidationError as exc:
            raise ServiceError(
                "INVALID_RESPONSE",
                "Unexpected search response",
                "Report a catalog contract change",
            ) from exc
        cursor = None
        if result.after and page < 3:
            cursor = uuid4().hex
            self.cursors[cursor] = (time.monotonic(), signature, result.after, page + 1)
            if len(self.cursors) > 128:
                self.cursors.popitem(last=False)
        return {
            "datasets": [card(item) for item in result.results[: request.limit]],
            "next_cursor": cursor,
            "page": page,
            "page_budget_reached": bool(result.after and page == 3),
            "applied_filters": signature,
            "provenance": meta,
            "scope": "Metadata search; inspect observation periods and joinability",
            "source_text_is_untrusted": True,
        }

    async def inspect(self, record_id: str):
        try:
            record_id = str(UUID(record_id))
        except ValueError as exc:
            raise ServiceError(
                "INVALID_ID",
                "Expected a harvest-record UUID",
                "Use harvest_record_id returned by search",
            ) from exc
        body, meta = await self.http.get("/harvest_record/" + record_id)
        transformed = body.get("source_transform")
        source = (
            transformed if isinstance(transformed, dict) else body.get("source_raw")
        )
        if isinstance(source, str):
            try:
                source = json.loads(source)
            except ValueError as exc:
                raise ServiceError(
                    "UNSUPPORTED_METADATA",
                    "Source metadata is not JSON",
                    "Inspect the catalog landing page",
                ) from exc
        if not isinstance(source, dict):
            raise ServiceError(
                "UNSUPPORTED_METADATA",
                "No usable dataset object",
                "Inspect the catalog landing page",
            )
        result = card({"dcat": source}, detail=True)
        result["harvest_record_id"] = record_id
        return {
            "dataset": result,
            "provenance": meta,
            "metadata_form": "transformed" if isinstance(transformed, dict) else "raw",
        }

    async def vocabulary(self, kind: str, query: str):
        if kind == "organizations":
            body, meta = await self.http.get(self.api_path("organizations"), ttl=86400)
            items = body.get("organizations")
            if isinstance(items, list):
                items = [
                    item
                    for item in items
                    if isinstance(item, dict)
                    and query.casefold() in json.dumps(item).casefold()
                ]
                items = [
                    {
                        k: item.get(k)
                        for k in ("slug", "name", "organization_type", "dataset_count")
                    }
                    for item in items[:10]
                ]
        elif kind == "locations":
            body, meta = await self.http.get(
                self.api_path("locations/search"), {"q": query, "size": 5}, ttl=86400
            )
            items = body.get("locations")
        else:
            body, meta = await self.http.get(
                self.api_path("keywords"), {"search": query, "size": 10}, ttl=86400
            )
            items = body.get("keywords")
        if not isinstance(items, list) or any(not isinstance(i, dict) for i in items):
            raise ServiceError(
                "INVALID_RESPONSE",
                "Unexpected vocabulary response",
                "Report a catalog contract change",
            )
        return {"kind": kind, "matches": items[:10], "provenance": meta}
