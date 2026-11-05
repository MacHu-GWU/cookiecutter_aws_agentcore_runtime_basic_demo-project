# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import make_agent
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import (
    build_agent,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import app
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import invoke
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import main

import boto3
import pytest
from starlette.exceptions import HTTPException

from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes import site_agent
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.common import ProcessAgent
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.mcp_connection import (
    get_runtime_arn_env_var,
)

TOOL_NAMES = [
    "get_site",
    "get_technician",
    "get_weather",
    "list_assets",
    "list_sites",
]


def test_mcp_arn_env_var(config: Config):
    """The variable bind() sets for PowerPlantMcp, named in cdk-stack.ts."""
    name = config.agentcore_runtime_name_power_plant_mcp
    assert get_runtime_arn_env_var(name) == "AGENTCORE_RUNTIME_POWERPLANTMCP_ARN"


def test_make_agent(mcp_url):
    """The agent has its own tools and the MCP tools, loaded over HTTP; no LLM call."""
    session = boto3.Session(region_name="us-east-1")
    agent = make_agent("us.amazon.nova-2-lite-v1:0", session, mcp_url)
    try:
        assert sorted(agent.tool_names) == TOOL_NAMES
    finally:
        agent.cleanup()


def test_build_agent(mcp_url, monkeypatch):
    """With the dependencies of the process: here the local MCP server of MCP_URL_POWERPLANTMCP."""
    monkeypatch.setenv("MCP_URL_POWERPLANTMCP", mcp_url)
    agent = build_agent()
    try:
        assert sorted(agent.tool_names) == TOOL_NAMES
    finally:
        agent.cleanup()


class FakeAgent:
    def __call__(self, prompt):
        return f"<thinking>hmm</thinking> answer to {prompt}"

    def cleanup(self):
        pass


def test_invoke(monkeypatch):
    """The answer of the agent of the process, without the model's thinking."""
    monkeypatch.setattr(site_agent, "agent", ProcessAgent(FakeAgent))
    assert invoke({"prompt": "hi"}) == {"result": "answer to hi"}


def test_invoke_bad_payload(monkeypatch):
    """A payload that does not validate is a 400 naming the field; no agent is built."""
    built = []
    monkeypatch.setattr(site_agent, "agent", ProcessAgent(lambda: built.append(1)))
    with pytest.raises(HTTPException) as info:
        invoke({"question": "hi"})
    assert info.value.status_code == 400
    assert info.value.detail[0]["loc"] == ("prompt",)
    assert built == []


def test_main(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(app, "run", lambda: calls.append("run"))
    main()
    assert calls == ["run"]
    assert "Loaded the config of 'dev'" in capsys.readouterr().out


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent",
        preview=False,
    )
