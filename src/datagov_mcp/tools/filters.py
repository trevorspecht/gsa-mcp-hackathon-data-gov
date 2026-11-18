from typing import Annotated, Literal

from pydantic import Field

from datagov_mcp.tools.common import guarded


def register(mcp, services):
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    @guarded
    async def suggest_search_filters(
        kind: Literal["organizations", "keywords", "locations"],
        query: Annotated[str, Field(min_length=1, max_length=100)],
    ) -> dict:
        """Resolve a publisher, topic or place into catalog filters before searching.

        Returns at most ten vocabulary entries (five locations), cached for 24 hours.
        Location IDs are opaque strings; geographic matching tests metadata extents,
        not whether a dataset contains the requested county-level observations.
        """
        return await services.catalog.vocabulary(kind, query)
