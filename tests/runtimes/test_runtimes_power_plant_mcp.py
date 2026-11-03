# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.power_plant_mcp import mcp
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.power_plant_mcp import main

import pytest

import json
import asyncio

from mcp.server.fastmcp.exceptions import ToolError


def test_list_tools():
    tools = asyncio.run(mcp.list_tools())
    names = sorted(tool.name for tool in tools)
    assert names == ["get_site", "get_technician", "list_assets", "list_sites"]


def test_call_tool():
    """A tool call goes through the MCP layer and returns the query result as JSON text."""
    content = asyncio.run(mcp.call_tool("get_site", {"site_id": "S-03"}))
    site = json.loads(content[0].text)
    assert site["name"] == "Ridge Wind"
    assert len(site["technicians"]) == 2


def test_call_tool_not_found():
    with pytest.raises(ToolError, match="site 'S-99' not found"):
        asyncio.run(mcp.call_tool("get_site", {"site_id": "S-99"}))


def test_main(monkeypatch):
    calls = []
    monkeypatch.setattr(mcp, "run", lambda transport: calls.append(transport))
    main()
    assert calls == ["streamable-http"]


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.power_plant_mcp",
        preview=False,
    )
