from datagov_mcp.models import CompareRequest
from datagov_mcp.tools.common import guarded


def register(mcp, services):
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    @guarded
    def assess_comparison(request: CompareRequest) -> dict:
        """Check whether registered indicators support a descriptive county comparison.

        Checks metrics, geography, periods and snapshot readiness; returns reasons when
        unsupported. Population is July 1; unemployment is annual average. A comparison
        cannot establish causation. Consult data.gov://capabilities for supported IDs.
        """
        return services.registry.assess(request)
