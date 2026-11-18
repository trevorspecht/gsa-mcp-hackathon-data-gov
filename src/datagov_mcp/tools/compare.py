from datagov_mcp.models import CompareRequest
from datagov_mcp.tools.common import guarded


def register(mcp, services):
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    @guarded
    async def compare_public_indicators(request: CompareRequest) -> dict:
        """Compare registered population and unemployment indicators in Databricks.

        Runs only reviewed parameterized SQL for a verified snapshot; returns summary
        counts over all compared counties (quote these for any "how many counties"
        claim), filtered rows, missing coverage, units and evidence ID. Population
        change is percent; rate change is percentage points. Refuses unsupported or
        unconfigured requests.
        Use get_analysis_evidence to reproduce the result and cite source versions.
        """
        return await services.analytics.compare(request)
