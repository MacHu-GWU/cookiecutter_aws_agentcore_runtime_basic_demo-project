# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.power_plant_mcp import mcp
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.power_plant_mcp import main

import pytest

import json
import asyncio

from mcp.server.fastmcp.exceptions import ToolError

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant import queries


def test_list_tools():
    tools = asyncio.run(mcp.list_tools())
    names = sorted(tool.name for tool in tools)
    assert names == ["get_site", "get_technician", "list_assets", "list_sites"]
    for tool in tools:
        # the description is the query's docstring; the engine is not a parameter
        assert tool.description.strip() == getattr(queries, tool.name).__doc__.strip()
        assert "engine" not in tool.inputSchema["properties"]
        # the output schema comes from the Pydantic return type
        assert tool.outputSchema is not None


@pytest.mark.parametrize(
    "name, arguments, expected_ids",
    [
        ("list_sites", {"kind": "wind"}, ["S-03", "S-04"]),
        ("list_assets", {"site_id": "S-03"}, ["A-06", "A-07", "A-08"]),
    ],
)
def test_call_list_tool(name, arguments, expected_ids):
    """
    A list tool reaches its query through one.engine; FastMCP wraps a list
    result in the structured output, ``{"result": [...]}``.
    """
    _, structured = asyncio.run(mcp.call_tool(name, arguments))
    assert [row["id"] for row in structured["result"]] == expected_ids


def test_call_tool_get_technician():
    _, technician = asyncio.run(
        mcp.call_tool("get_technician", {"technician_id": "T-02"})
    )
    assert [row["id"] for row in technician["sites"]] == ["S-03"]


def test_call_tool_get_site():
    """
    A tool call goes through the MCP layer and returns the model both as JSON
    text (for clients that read only text) and as structured output.
    """
    content, site = asyncio.run(mcp.call_tool("get_site", {"site_id": "S-03"}))
    assert json.loads(content[0].text) == site
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
