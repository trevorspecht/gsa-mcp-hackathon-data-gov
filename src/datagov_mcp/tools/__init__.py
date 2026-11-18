"""Explicit registration is tested through the MCP protocol."""

from datagov_mcp.tools import assess, compare, evidence, filters, inspect, search


def register_tools(mcp, services):
    for module in (search, inspect, filters, assess, compare, evidence):
        module.register(mcp, services)
