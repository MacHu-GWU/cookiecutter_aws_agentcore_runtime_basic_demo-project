# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.mcp_client import (
    list_tools,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.mcp_client import (
    call_tool,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.mcp_client import main

import json

import pytest


def test_list_tools(mcp_url):
    assert sorted(list_tools(mcp_url)) == [
        "get_site",
        "get_technician",
        "list_assets",
        "list_sites",
    ]


def test_call_tool(mcp_url):
    site = call_tool(mcp_url, "get_site", {"site_id": "S-03"})
    assert site["name"] == "Ridge Wind"
    sites = call_tool(mcp_url, "list_sites", {"kind": "wind"})
    assert [row["id"] for row in sites["result"]] == ["S-03", "S-04"]
    with pytest.raises(RuntimeError, match="site 'S-99' not found"):
        call_tool(mcp_url, "get_site", {"site_id": "S-99"})


def test_main(mcp_url, capsys):
    args = ["--url", mcp_url, "--tool", "get_site"]
    assert main(args + ["--arguments", json.dumps({"site_id": "S-03"})]) == 0
    out = capsys.readouterr().out
    assert "tool: get_site" in out
    assert '"name": "Ridge Wind"' in out
    assert main(args + ["--arguments", json.dumps({"site_id": "S-99"})]) == 1
    assert "error: " in capsys.readouterr().out


def test_main_url_from_env(mcp_url, monkeypatch, capsys):
    monkeypatch.setenv("MCP_URL", mcp_url)
    assert main(["--tool", "list_sites"]) == 0
    assert f"MCP server: {mcp_url}" in capsys.readouterr().out


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.devtools.mcp_client",
        preview=False,
    )
