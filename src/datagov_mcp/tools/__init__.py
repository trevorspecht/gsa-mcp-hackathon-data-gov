"""Explicit registration is tested through the MCP protocol."""

from datagov_mcp.tools import (
    assess,
    compare,
    evidence,
    filters,
    inspect,
    science,
    search,
)


def register_tools(mcp, services):
    for module in (search, inspect, filters, assess, compare, evidence, science):
        module.register(mcp, services)
