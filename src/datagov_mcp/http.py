"""Fixed-origin HTTP with byte, time, concurrency, cache and request budgets."""

import asyncio
import copy
import json
import logging
import re
import time
from collections import OrderedDict, deque
from datetime import datetime, timezone

import httpx

from datagov_mcp.config import Settings
from datagov_mcp.errors import ServiceError
from datagov_mcp.tls import verified_context

logger = logging.getLogger(__name__)
MAX_BYTES = 5_000_000


class CatalogHTTP:
    def __init__(self, settings: Settings, transport=None):
        self.settings = settings
        self.transport = transport
        self.cache = OrderedDict()
        self.requests = deque()
        self.semaphore = asyncio.Semaphore(2)

    async def get(self, path: str, params=None, ttl: int = 900) -> tuple[dict, dict]:
        if not re.fullmatch(r"/[A-Za-z0-9_/-]+", path) or ".." in path:
            raise ServiceError("INVALID_PATH", "Invalid catalog path", "Use a tool ID")
        key = (path, json.dumps(params, sort_keys=True))
        now = time.monotonic()
        if key in self.cache:
            created, body, meta = self.cache[key]
            if now - created < ttl:
                self.cache.move_to_end(key)
                return copy.deepcopy(body), {
                    **meta,
                    "cache_hit": True,
                    "cache_age_seconds": round(now - created, 2),
                }
            del self.cache[key]
        async with self.semaphore:
            self._budget()
            body, meta = await self._fetch(path, params)
        self.cache[key] = (time.monotonic(), copy.deepcopy(body), meta)
        if len(self.cache) > 128:
            self.cache.popitem(last=False)
        return body, meta

    def _budget(self):
        now = time.monotonic()
        while self.requests and now - self.requests[0] >= 3600:
            self.requests.popleft()
        if len(self.requests) >= self.settings.catalog_requests_per_hour:
            raise ServiceError(
                "LOCAL_RATE_LIMIT",
                "Catalog request budget exhausted",
                "Wait for the rolling hourly budget; cached queries remain available",
            )
        self.requests.append(now)

    async def _fetch(self, path: str, params) -> tuple[dict, dict]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "datagov-semantic-mcp/0.1",
        }
        if self.settings.catalog_interface == "gateway":
            key = self.settings.data_gov_api_key.get_secret_value()
            if not key or key == "DEMO_KEY":
                raise ServiceError(
                    "SETUP_REQUIRED",
                    "A personal API key is required",
                    "Set DATA_GOV_API_KEY for the selected gateway",
                )
            headers["X-Api-Key"] = key
        try:
            async with asyncio.timeout(30):
                async with httpx.AsyncClient(
                    timeout=20,
                    follow_redirects=False,
                    trust_env=False,
                    transport=self.transport,
                    verify=verified_context(),
                ) as client:
                    return await self._read(client, path, params, headers)
        except (httpx.HTTPError, TimeoutError) as exc:
            raise ServiceError(
                "UPSTREAM_UNAVAILABLE",
                "Catalog request failed",
                "Check approved network access and retry later",
            ) from exc

    async def _read(self, client, path, params, headers):
        async with client.stream(
            "GET", self.settings.catalog_origin + path, params=params, headers=headers
        ) as response:
            status = response.status_code
            logger.info(
                json.dumps(
                    {
                        "event": "catalog_request",
                        "status": status,
                        "interface": self.settings.catalog_interface,
                    }
                )
            )
            if status != 200:
                codes = {
                    404: "NOT_FOUND",
                    429: "UPSTREAM_RATE_LIMIT",
                    401: "UPSTREAM_AUTH",
                    403: "UPSTREAM_AUTH",
                }
                raise ServiceError(
                    codes.get(status, "UPSTREAM_ERROR"),
                    f"Catalog returned HTTP {status}",
                    "Check filters, access and quota; redirects are disabled",
                )
            if "json" not in response.headers.get("content-type", "").lower():
                raise ServiceError(
                    "INVALID_RESPONSE",
                    "Expected catalog JSON",
                    "Check the configured interface",
                )
            content = bytearray()
            async for chunk in response.aiter_bytes():
                content.extend(chunk)
                if len(content) > MAX_BYTES:
                    raise ServiceError(
                        "RESPONSE_TOO_LARGE",
                        "Catalog response exceeded 5 MB",
                        "Narrow the search",
                    )
            try:
                body = json.loads(content)
                if not isinstance(body, dict):
                    raise ValueError("Expected object")
            except (ValueError, UnicodeError) as exc:
                raise ServiceError(
                    "INVALID_RESPONSE",
                    "Invalid catalog JSON object",
                    "Retry later or report an upstream contract change",
                ) from exc
            remaining = response.headers.get("x-ratelimit-remaining", "")
            return body, {
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "interface": self.settings.catalog_interface,
                "cache_hit": False,
                "cache_age_seconds": 0,
                "rate_limit_remaining": int(remaining) if remaining.isdigit() else None,
            }
