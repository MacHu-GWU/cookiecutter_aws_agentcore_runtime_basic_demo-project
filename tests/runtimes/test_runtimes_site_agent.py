# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import (
    LOCAL_MCP_URL,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import (
    get_weather,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import (
    get_mcp_url,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import make_agent
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import app
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import invoke
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import main

import pytest

import time
import socket
import threading

import uvicorn

from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes import site_agent
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.power_plant_mcp import mcp


@pytest.fixture(scope="module")
def mcp_url():
    """Run the real PowerPlantMcp server on a free local port for this module."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    config = uvicorn.Config(
        mcp.streamable_http_app(),
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/mcp"
    server.should_exit = True
    thread.join()


def test_get_weather():
    assert get_weather.tool_name == "get_weather"
    assert get_weather(41.1, -105.9)["safe_for_inspection"] is False


def test_get_mcp_url(monkeypatch):
    monkeypatch.delenv("MCP_URL", raising=False)
    assert get_mcp_url() == LOCAL_MCP_URL
    monkeypatch.setenv("MCP_URL", "http://example.com/mcp")
    assert get_mcp_url() == "http://example.com/mcp"


def test_make_agent(monkeypatch, mcp_url):
    """The agent loads the MCP tools over HTTP; no LLM call is made."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    agent = make_agent(mcp_url)
    try:
        assert sorted(agent.tool_names) == [
            "get_site",
            "get_technician",
            "get_weather",
            "list_assets",
            "list_sites",
        ]
    finally:
        agent.cleanup()


class FakeAgent:
    def __init__(self):
        self.cleaned = False

    def __call__(self, prompt):
        return f"answer to {prompt}"

    def cleanup(self):
        self.cleaned = True


def test_invoke(monkeypatch):
    fake_agent = FakeAgent()
    monkeypatch.setattr(site_agent, "make_agent", lambda mcp_url: fake_agent)
    assert invoke({"prompt": "hi"}) == {"result": "answer to hi"}
    assert fake_agent.cleaned is True


def test_main(monkeypatch):
    calls = []
    monkeypatch.setattr(app, "run", lambda: calls.append("run"))
    main()
    assert calls == ["run"]


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent",
        preview=False,
    )
