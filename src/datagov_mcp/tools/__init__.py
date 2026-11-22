"""Explicit registration is tested through the MCP protocol."""

from datagov_mcp.tools import (
    assess,
    compare,
    evidence,
    explore,
    filters,
    inspect,
    readiness,
    science,
    search,
)


def register_tools(mcp, services):
    for module in (
        search,
        inspect,
        filters,
        assess,
        compare,
        evidence,
        science,
        readiness,
        explore,
    ):
        module.register(mcp, services)
