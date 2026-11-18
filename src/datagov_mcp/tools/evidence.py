from typing import Annotated

from pydantic import Field

from datagov_mcp.tools.common import guarded


def register(mcp, services):
    @mcp.tool(annotations={"readOnlyHint": True, "openWorldHint": False})
    @guarded
    def get_analysis_evidence(
        evidence_id: Annotated[str, Field(pattern=r"^[a-f0-9]{32}$")],
    ) -> dict:
        """Retrieve saved SQL, parameters, source hashes, definitions and result rows.

        Evidence is public-data material accessible within the App permission boundary.
        It is stored locally: download it before an ephemeral App restart.
        """
        return services.evidence.get(evidence_id)
