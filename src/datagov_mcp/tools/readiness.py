"""Readiness is distinct from catalog relevance and question compatibility."""

from typing import Annotated
from uuid import UUID

from pydantic import Field

from datagov_mcp.readiness import ranked
from datagov_mcp.tools.common import guarded


def register(mcp, services):
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    @guarded
    async def assess_dataset_readiness(
        question: Annotated[str, Field(min_length=1, max_length=2000)],
        harvest_record_ids: Annotated[list[UUID], Field(min_length=1, max_length=5)],
    ) -> dict:
        """Rank up to five discovered candidates and assess query readiness.

        Supply search result harvest UUIDs and the user's original question. Fetches
        bounded catalog metadata only, never distribution URLs. Ranking is explicit
        keyword overlap, not a whole-catalog semantic ranking or confidence score.
        Exact reviewed bindings expose narrow snapshot scopes; API/file hints stay
        unverified without a connector. Ready does not mean the question is answerable:
        check years, geography, measures and connector validation before querying.
        """
        datasets = []
        for identity in harvest_record_ids:
            result = await services.catalog.inspect(str(identity))
            datasets.append(result["dataset"])
        return {
            "datasets": ranked(question, datasets, services.datasets),
            "scope": (
                "Ranked inspected candidates only; no publisher endpoint was fetched"
            ),
            "source_text_is_untrusted": True,
        }
