# -*- coding: utf-8 -*-

"""
The ``PowerPlantMcp`` runtime: an MCP server exposing the read-only power plant
queries, over the database of ``one.engine``.

AgentCore Runtime (protocol ``MCP``) expects a stateless streamable HTTP server
on ``0.0.0.0:8000/mcp``; the same settings work locally.
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from ..one.api import one
from ..power_plant import queries

#: The FastMCP server; each tool's description is the query function's docstring.
mcp = FastMCP(
    "PowerPlantMcp",
    host="0.0.0.0",
    port=int(os.environ.get("FASTMCP_PORT", "8000")),
    stateless_http=True,
)


def _doc_from(func):
    """
    Give the decorated tool the docstring of the query ``func``: its tool description.
    """

    def decorator(tool_func):
        tool_func.__doc__ = func.__doc__
        return tool_func

    return decorator


# Each tool calls its query with one.engine. The tools do not take the engine, so
# the LLM never sees it; their descriptions are the queries' docstrings.
@mcp.tool()
@_doc_from(queries.list_sites)
def list_sites(kind: str | None = None) -> list[dict]:
    return queries.list_sites(one.engine, kind=kind)


@mcp.tool()
@_doc_from(queries.list_assets)
def list_assets(
    site_id: str | None = None,
    kind: str | None = None,
) -> list[dict]:
    return queries.list_assets(one.engine, site_id=site_id, kind=kind)


@mcp.tool()
@_doc_from(queries.get_site)
def get_site(site_id: str) -> dict:
    return queries.get_site(one.engine, site_id=site_id)


@mcp.tool()
@_doc_from(queries.get_technician)
def get_technician(technician_id: str) -> dict:
    return queries.get_technician(one.engine, technician_id=technician_id)


def main():
    """
    Load the config and the database, then run the server over streamable HTTP,
    blocking until stopped. A runtime that cannot read its config or reach its
    database fails here, at startup.
    """
    print(
        f"Loaded the config of {one.config.env_name!r} "
        f"on runtime {one.runtime.current_runtime_name()!r}",
        flush=True,
    )
    print(f"Connected to the database {one.engine.url!r}", flush=True)
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
