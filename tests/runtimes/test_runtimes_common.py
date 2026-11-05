# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.common import MCP_PORT_VAR
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.common import get_mcp_port
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.common import (
    new_mcp_server,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.common import (
    run_mcp_server,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.common import doc_from
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.common import (
    print_config_source,
)

import asyncio


def test_get_mcp_port(monkeypatch):
    # the name is a contract with agentcore dev and the mise tasks
    assert MCP_PORT_VAR == "FASTMCP_PORT"
    monkeypatch.delenv("FASTMCP_PORT", raising=False)
    assert get_mcp_port() == 8000
    monkeypatch.setenv("FASTMCP_PORT", "18731")
    assert get_mcp_port() == 18731


def test_new_mcp_server(monkeypatch):
    """The settings of the AgentCore MCP protocol contract."""
    monkeypatch.delenv("FASTMCP_PORT", raising=False)
    mcp = new_mcp_server("MyMcp")
    assert mcp.name == "MyMcp"
    assert mcp.settings.host == "0.0.0.0"
    assert mcp.settings.port == 8000
    assert mcp.settings.streamable_http_path == "/mcp"
    assert mcp.settings.stateless_http is True


def test_run_mcp_server(monkeypatch):
    mcp = new_mcp_server("MyMcp")
    calls = []
    monkeypatch.setattr(mcp, "run", lambda transport: calls.append(transport))
    run_mcp_server(mcp)
    assert calls == ["streamable-http"]


def add(engine, a: int, b: int) -> int:
    """
    Add two numbers.
    """
    return a + b


def test_doc_from():
    """The tool takes the description, not the signature, of the function."""
    mcp = new_mcp_server("MyMcp")

    @mcp.tool()
    @doc_from(add)
    def add_tool(a: int, b: int) -> int:
        return add(None, a, b)

    (tool,) = asyncio.run(mcp.list_tools())
    assert tool.description.strip() == "Add two numbers."
    assert sorted(tool.inputSchema["properties"]) == ["a", "b"]


def test_print_config_source(capsys):
    print_config_source()
    assert capsys.readouterr().out == "Loaded the config of 'dev' on runtime 'local'\n"


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.common",
        preview=False,
    )
