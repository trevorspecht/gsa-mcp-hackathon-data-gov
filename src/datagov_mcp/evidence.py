"""Bounded local evidence. Public-data artifacts share the App's access boundary."""

import json
import re
from datetime import datetime, timezone
from uuid import uuid4

from datagov_mcp.errors import ServiceError


class EvidenceStore:
    def __init__(self, directory):
        self.directory = directory

    def save(self, payload):
        evidence_id = uuid4().hex
        content = json.dumps(
            {
                "evidence_id": evidence_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                **payload,
            },
            allow_nan=False,
        )
        if len(content.encode()) > 64_000:
            raise ServiceError(
                "EVIDENCE_TOO_LARGE",
                "Evidence exceeds output budget",
                "Narrow the analysis",
            )
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            if sum(1 for _ in self.directory.glob("*.json")) >= 1000:
                raise ServiceError(
                    "EVIDENCE_CAPACITY",
                    "Evidence store is full",
                    "Operator must archive evidence before continuing",
                )
            with (self.directory / f"{evidence_id}.json").open("x") as output:
                output.write(content)
        except OSError as exc:
            raise ServiceError(
                "EVIDENCE_STORAGE",
                "Could not persist evidence",
                "Check the configured evidence directory",
            ) from exc
        return evidence_id

    def get(self, evidence_id):
        if not re.fullmatch(r"[a-f0-9]{32}", evidence_id):
            raise ServiceError(
                "INVALID_ID", "Invalid evidence ID", "Use the returned evidence_id"
            )
        try:
            path = self.directory / f"{evidence_id}.json"
            if path.stat().st_size > 64_000:
                raise ValueError("Oversized evidence")
            return json.loads(path.read_text())
        except FileNotFoundError as exc:
            raise ServiceError(
                "NOT_FOUND",
                "Evidence is not present in this server",
                "Evidence is local; preserve it before an App restart",
            ) from exc
        except (OSError, ValueError) as exc:
            raise ServiceError(
                "EVIDENCE_STORAGE",
                "Evidence is unreadable",
                "Ask the operator to inspect the evidence store",
            ) from exc
