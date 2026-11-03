# -*- coding: utf-8 -*-

"""
The ``PowerPlantMcp`` runtime: an MCP server exposing the read-only power plant queries.

AgentCore Runtime (protocol ``MCP``) expects a stateless streamable HTTP server
on ``0.0.0.0:8000/mcp``; the same settings work locally.
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from ..power_plant import queries

#: The FastMCP server; each tool's description is the query function's docstring.
mcp = FastMCP(
    "PowerPlantMcp",
    host="0.0.0.0",
    port=int(os.environ.get("FASTMCP_PORT", "8000")),
    stateless_http=True,
)

mcp.tool()(queries.list_sites)
mcp.tool()(queries.list_assets)
mcp.tool()(queries.get_site)
mcp.tool()(queries.get_technician)


def main():
    """
    Run the server over streamable HTTP, blocking until stopped.
    """
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
