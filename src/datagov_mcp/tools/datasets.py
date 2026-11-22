from typing import Annotated

from pydantic import Field

from datagov_mcp.models import ChangeRequest, CompatibilityRequest, ObservationRequest
from datagov_mcp.tools.common import guarded


def register(mcp, services):
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    @guarded
    def list_queryable_datasets(
        query: Annotated[str, Field(max_length=300)] = "",
    ) -> dict:
        """List reviewed datasets that can return observations, with measures,
        units, definitions, geography, periods, readiness and caveats.

        Optional query narrows by registry keywords. Use returned dataset/measure IDs
        with query_dataset, analyze_change and assess_compatibility. Catalog search
        results outside this list are discovery only and cannot be queried.
        """
        datasets = [
            services.datasets.describe(d) for d in services.datasets.data["datasets"]
        ]
        if query.strip():
            matched = {m["dataset_id"] for m in services.datasets.search_terms(query)}
            datasets = [d for d in datasets if d["dataset_id"] in matched] or datasets
        return {
            "datasets": datasets,
            "scope": "Reviewed registry only; geography and periods are fixed coverage",
        }

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    @guarded
    async def query_dataset(request: ObservationRequest, live: bool = False) -> dict:
        """Return observations for a reviewed dataset, filtered by measure,
        geography ID and period, with units, sources and an evidence ID.

        Missing values stay missing. live=true refreshes from the dataset's fixed
        reviewed publisher route only when the user asks for current/live data;
        otherwise the reviewed snapshot is used. No SQL, table names or URLs.
        """
        return await services.datasets.observations(request, live=live)

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": True})
    @guarded
    async def analyze_change(request: ChangeRequest) -> dict:
        """Compute start-to-end change per geography for registered measures.

        Uses each measure's registered definition (percent or difference). Returns
        direction counts over every complete geography — quote these for any count —
        plus filtered/sorted rows, missing coverage, units and evidence. Endpoint
        change is not a trend or causal effect.
        """
        return await services.datasets.change(request)

    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    @guarded
    def assess_compatibility(request: CompatibilityRequest) -> dict:
        """Check whether selected reviewed datasets share geography, periods and
        readiness for side-by-side description. Never computes correlations,
        joins or causal estimates; explains mismatches and next steps.
        """
        return services.datasets.compatibility(request)
