from typing import Annotated

from pydantic import Field

from datagov_mcp.tools.common import guarded


def register(mcp, services):
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    @guarded
    async def inspect_dataset(
        harvest_record_id: Annotated[str, Field(min_length=36, max_length=36)],
    ) -> dict:
        """Inspect a search result's harvest-record UUID, not its publisher identifier.

        Returns bounded metadata, distributions, distribution terms and source dates.
        Uses the transformed payload when present, otherwise labels the raw JSON.
        Does not follow distribution URLs. Missing rights never authorize data fetching.
        """
        return await services.catalog.inspect(harvest_record_id)
