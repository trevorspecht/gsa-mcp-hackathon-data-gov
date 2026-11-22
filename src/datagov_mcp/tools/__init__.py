"""Explicit registration is tested through the MCP protocol."""

from datagov_mcp.tools import datasets, evidence, filters, inspect, readiness, search


def register_tools(mcp, services):
    for module in (search, inspect, filters, readiness, datasets, evidence):
        module.register(mcp, services)
