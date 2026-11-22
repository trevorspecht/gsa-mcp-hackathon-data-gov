"""Explainable candidate ranking and reviewed access routes, never URL execution."""

import re

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "data",
    "dataset",
    "datasets",
    "do",
    "does",
    "find",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "show",
    "that",
    "the",
    "these",
    "this",
    "to",
    "was",
    "were",
    "what",
    "which",
    "with",
}


def terms(text):
    return set(re.findall(r"[a-z0-9]+", text.casefold())) - STOPWORDS


def relevance(question, dataset):
    requested = terms(question)
    title = requested & terms(dataset.get("title") or "")
    description = requested & terms(dataset.get("description") or "")
    coverage = requested & terms(
        " ".join(
            str(dataset.get(key) or "")
            for key in ("keywords", "observation_period", "spatial_coverage")
        )
    )
    return {
        "score": 3 * len(title) + len(description) + len(coverage),
        "title_matches": sorted(title),
        "description_matches": sorted(description),
        "coverage_keyword_matches": sorted(coverage),
        "unmatched_question_terms": sorted(requested - title - description - coverage),
        "method": "Keyword overlap: title ×3, description ×1, coverage/keywords ×1",
        "limitation": (
            "Ranking of inspected candidates only, not the whole catalog. "
            "Not a probability or proof of geographic, temporal "
            "or measure compatibility."
        ),
    }


def assess(dataset, datasets):
    scopes = [
        {
            "dataset_id": scope["dataset_id"],
            "title": scope["title"],
            "geography": scope["geography"],
            "available_periods": scope["periods"],
            "measures": [
                {"id": m["id"], "label": m["label"], "unit": m["unit"]}
                for m in scope["measures"]
            ],
            "storage": scope["storage"],
            "setup_blockers": scope["setup_blockers"],
        }
        for scope in datasets.catalog_scopes(dataset.get("identifier"))
    ]
    available = [scope for scope in scopes if not scope.get("setup_blockers")]
    routes = []
    for distribution in dataset.get("distributions", []):
        for key, kind in (
            ("download_url", "file"),
            ("access_url", "access page or API"),
        ):
            if distribution.get(key):
                routes.append(
                    {
                        "kind": kind,
                        "url": distribution[key],
                        "format": distribution.get("format"),
                        "byte_size": distribution.get("byte_size"),
                        "terms": distribution.get("terms", {}),
                        "verified": False,
                    }
                )
        if distribution.get("access_service"):
            routes.append(
                {
                    "kind": "advertised data service",
                    "description": distribution["access_service"],
                    "terms": distribution.get("terms", {}),
                    "verified": False,
                }
            )
    if available:
        status, label = "ready_within_reviewed_scope", "Ready within reviewed scope"
        blockers = []
    elif scopes:
        status, label = "setup_required", "Reviewed connector — setup required"
        blockers = sorted(
            {b for scope in scopes for b in scope.get("setup_blockers", [])}
        )
    elif dataset.get("access_status") == "restricted":
        status, label = "setup_required", "Access review/setup required"
        blockers = [
            "Metadata reports restricted access; review authorization and terms"
        ]
    elif routes:
        status, label = "access_unverified", "Promising access route — unverified"
        blockers = [
            "No reviewed retrieval connector for this catalog record",
            "Endpoint availability, authentication, size, schema "
            "and terms are unverified",
        ]
    else:
        status, label = "metadata_only", "Metadata only — access unknown"
        blockers = ["No reviewed connector or usable distribution route established"]
    return {
        "status": status,
        "label": label,
        "scopes": scopes,
        "advertised_routes": routes,
        "blockers": blockers,
        "estimated_wait_seconds": None,
        "wait_note": (
            "No timed live retrieval estimate; metadata links have not been fetched"
        ),
        "question_compatibility": (
            "Not established; inspect scope and use the connector's validation"
        ),
        "binding_basis": (
            "Exact reviewed publisher catalog identifier, never title similarity"
        ),
        "limitations": [
            "Ready means only the listed registered scopes, "
            "not the entire publisher dataset",
            "An advertised public API/file is not proof "
            "of executable or permitted access",
            "No arbitrary downloads, SQL or database connections are performed",
        ],
    }


def ranked(question, records, datasets):
    unique = {}
    for dataset in records:
        key = dataset.get("identifier") or dataset["harvest_record_id"]
        assessed = {
            **dataset,
            "relevance": relevance(question, dataset),
            "readiness": assess(dataset, datasets),
        }
        assessed["queryable"] = (
            assessed["readiness"]["status"] == "ready_within_reviewed_scope"
        )
        assessed["queryability_reason"] = (
            assessed["readiness"]["label"] + "; see exact scopes"
        )
        unique.setdefault(key, assessed)
    ordered = sorted(
        unique.values(), key=lambda d: (-d["relevance"]["score"], d.get("title") or "")
    )
    return [
        {**dataset, "candidate_rank": index} for index, dataset in enumerate(ordered, 1)
    ]
