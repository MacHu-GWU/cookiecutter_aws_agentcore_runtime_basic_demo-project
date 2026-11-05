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
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.common import (
    strip_thinking,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.common import ProcessAgent

import pytest

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


def test_strip_thinking():
    text = "<thinking> windy,\n so no </thinking>\n\nNo, too windy."
    assert strip_thinking(text) == "No, too windy."
    assert strip_thinking("<response> No. </response>") == "No."
    assert strip_thinking("plain") == "plain"


class FakeAgent:
    """Answers with the prompt; fails when told to; its cleanup fails too."""

    def __init__(self):
        self.prompts = []
        self.fail = False

    def __call__(self, prompt):
        if self.fail:
            raise ConnectionError("MCP connection lost")
        self.prompts.append(prompt)
        return f"answer to {prompt}"

    def cleanup(self):
        raise RuntimeError("a failing cleanup is ignored")


def test_process_agent():
    built = []

    def build():
        built.append(FakeAgent())
        return built[-1]

    agent = ProcessAgent(build)
    assert built == []  # nothing is built before the first call
    # one agent for every call of the process: one conversation
    assert agent("a") == "answer to a"
    assert agent("b") == "answer to b"
    assert len(built) == 1
    assert built[0].prompts == ["a", "b"]
    # a failing call drops the agent; the next call builds a new one
    built[0].fail = True
    with pytest.raises(ConnectionError):
        agent("c")
    assert agent("d") == "answer to d"
    assert len(built) == 2
    # reset without an agent does nothing
    agent.reset()
    agent.reset()


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.common",
        preview=False,
    )
