# -*- coding: utf-8 -*-

"""
The ``PowerPlantMcp`` runtime: an MCP server exposing the read-only power plant
queries of :mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.queries`.

A thin layer: each tool calls its query with the dependency it needs, the
database engine of the process (``one.engine``), injected here, so the LLM
never sees it. The description of a tool is its query's docstring, and its
output schema comes from the query's Pydantic return type.
"""

from __future__ import annotations

from ..one.api import one
from ..power_plant import queries
from ..power_plant.schemas import SiteInfo
from ..power_plant.schemas import AssetInfo
from ..power_plant.schemas import SiteDetail
from ..power_plant.schemas import TechnicianDetail
from .common import new_mcp_server
from .common import run_mcp_server
from .common import doc_from
from .common import print_config_source

#: The MCP server, named after the runtime in ``agentcore.json``.
mcp = new_mcp_server("PowerPlantMcp")


@mcp.tool()
@doc_from(queries.list_sites)
def list_sites(kind: str | None = None) -> list[SiteInfo]:
    return queries.list_sites(one.engine, kind=kind)


@mcp.tool()
@doc_from(queries.list_assets)
def list_assets(
    site_id: str | None = None,
    kind: str | None = None,
) -> list[AssetInfo]:
    return queries.list_assets(one.engine, site_id=site_id, kind=kind)


@mcp.tool()
@doc_from(queries.get_site)
def get_site(site_id: str) -> SiteDetail:
    return queries.get_site(one.engine, site_id=site_id)


@mcp.tool()
@doc_from(queries.get_technician)
def get_technician(technician_id: str) -> TechnicianDetail:
    return queries.get_technician(one.engine, technician_id=technician_id)


def main():
    """
    Load the config and the database, then serve, blocking until stopped. A
    runtime that cannot read its config or reach its database fails here, at
    startup.
    """
    print_config_source()
    print(f"Connected to the database {one.engine.url!r}", flush=True)
    run_mcp_server(mcp)


if __name__ == "__main__":
    main()
