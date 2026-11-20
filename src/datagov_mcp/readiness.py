"""Explainable candidate ranking and reviewed access routes, never URL execution."""

import re

from datagov_mcp.tools.science import snapshot

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


def assess(dataset, registry):
    identifier = dataset.get("identifier")
    science = snapshot()
    scopes = []
    for item in science["datasets"]:
        if identifier and identifier == item["source"].get("catalog_identifier"):
            scopes.append(
                {
                    "tool": "query_science_series",
                    "dataset_id": item["id"],
                    "title": item["title"],
                    "geography": item["geography"],
                    "available_years": [r["year"] for r in item["observations"]],
                    "unit": item["unit"],
                    "caveats": item["caveats"],
                    "storage": (
                        "Reviewed packaged historical snapshot, "
                        "not live publisher retrieval"
                    ),
                }
            )
    if identifier and any(
        identifier == source.get("catalog_identifier")
        for source in registry.data["sources"]
    ):
        capabilities = registry.capabilities()
        scopes.append(
            {
                "tool": "assess_comparison",
                "query_tool": "compare_public_indicators",
                "geography": "Maryland counties and county equivalents",
                "available_years": [2022, 2023, 2024],
                "measures": ["population", "unemployment_rate"],
                "storage": "Reviewed warehouse snapshot, not all publisher data",
                "setup_blockers": capabilities["setup_blockers"],
            }
        )
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
            "Ready means only the listed snapshot scopes, "
            "not the entire publisher dataset",
            "An advertised public API/file is not proof "
            "of executable or permitted access",
            "No arbitrary downloads, SQL or database connections are performed",
        ],
    }


def ranked(question, datasets, registry):
    unique = {}
    for dataset in datasets:
        key = dataset.get("identifier") or dataset["harvest_record_id"]
        assessed = {
            **dataset,
            "relevance": relevance(question, dataset),
            "readiness": assess(dataset, registry),
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
