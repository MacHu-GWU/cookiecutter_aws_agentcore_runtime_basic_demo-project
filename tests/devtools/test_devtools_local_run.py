# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_run import (
    get_local_url,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_run import (
    get_mcp_url_env,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_run import (
    get_local_command,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_run import (
    get_dev_command,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_run import (
    get_call_args,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_run import serve
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_run import run
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_run import main

import sys

import pytest

from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools import local_run
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_port import (
    PortHeldByOtherError,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.registry import (
    get_runtime_specs,
)

PKG = "cookiecutter_aws_agentcore_runtime_basic_demo"


@pytest.fixture
def specs(config: Config):
    mcp, agent = get_runtime_specs(config)
    return mcp, agent


@pytest.fixture
def executed(monkeypatch):
    """Record what serve() would exec, and free no port."""
    calls = []
    monkeypatch.setattr(local_run, "free_port", lambda port: [])
    monkeypatch.setattr(
        local_run.os, "execvpe", lambda file, argv, env: calls.append((argv, env))
    )
    return calls


def test_urls(specs):
    mcp, agent = specs
    assert get_local_url(mcp) == "http://localhost:18731/mcp"
    assert get_local_url(agent) == "http://localhost:18732"
    assert get_mcp_url_env(agent, list(specs)) == {
        "MCP_URL_POWERPLANTMCP": "http://localhost:18731/mcp"
    }
    assert get_mcp_url_env(mcp, list(specs)) == {}


def test_get_local_command(specs):
    mcp, agent = specs
    env, argv = get_local_command(mcp, list(specs))
    assert env == {"FASTMCP_PORT": "18731"}
    assert argv == [sys.executable, "-m", f"{PKG}.runtimes.power_plant_mcp"]
    env, argv = get_local_command(agent, list(specs))
    assert env == {"MCP_URL_POWERPLANTMCP": "http://localhost:18731/mcp"}
    assert argv[2:] == [
        "uvicorn",
        f"{PKG}.runtimes.site_agent:app",
        "--host",
        "127.0.0.1",
        "--port",
        "18732",
    ]


def test_get_dev_command(specs, config: Config):
    """The region of the config, an explicit port, and the agent's MCP URLs."""
    mcp, agent = specs
    env, argv = get_dev_command(agent, list(specs), config)
    assert env == {
        "AWS_REGION": "us-east-1",
        "MCP_URL_POWERPLANTMCP": "http://localhost:18731/mcp",
    }
    assert argv == [
        "agentcore",
        "dev",
        "--agent",
        "SiteAgent",
        "--no-traces",
        "--port",
        "18732",
    ]


def test_get_call_args(specs):
    mcp, agent = specs
    assert get_call_args(mcp) == [
        "--url",
        "http://localhost:18731/mcp",
        "--tool",
        "get_site",
        "--arguments",
        '{"site_id": "S-03"}',
    ]
    args = get_call_args(agent)
    assert args[:3] == ["--url", "http://localhost:18732", "--prompt"]


def test_serve(executed, monkeypatch, capsys):
    monkeypatch.setenv("KEEP_ME", "1")
    assert serve({"A": "b"}, ["prog", "--x"], port=18799) == 0
    ((argv, env),) = executed
    assert argv == ["prog", "--x"]
    assert env["A"] == "b" and env["KEEP_ME"] == "1"
    assert "A=b" in capsys.readouterr().out
    monkeypatch.setattr(local_run, "free_port", lambda port: [123])
    serve({}, ["prog"], port=18799)
    assert "stopped [123]" in capsys.readouterr().out


def test_serve_port_held_by_other(monkeypatch, capsys):
    def held(port):
        raise PortHeldByOtherError("held by someone else")

    monkeypatch.setattr(local_run, "free_port", held)
    assert serve({}, ["prog"], port=18799) == 1
    assert "held by someone else" in capsys.readouterr().out


def test_run(executed, config: Config, monkeypatch):
    assert run("PowerPlantMcp", "local", config) == 0
    assert run("SiteAgent", "dev", config) == 0
    assert executed[0][0][-1] == f"{PKG}.runtimes.power_plant_mcp"
    assert executed[1][0][:2] == ["agentcore", "dev"]
    calls = []
    monkeypatch.setattr(
        local_run.mcp_client, "main", lambda args: calls.append(args) or 0
    )
    monkeypatch.setattr(
        local_run.agent_client, "main", lambda args: calls.append(args) or 0
    )
    assert run("PowerPlantMcp", "call", config) == 0
    assert run("SiteAgent", "call", config) == 0
    assert "--tool" in calls[0] and "--prompt" in calls[1]
    with pytest.raises(ValueError, match="no runtime 'Missing'"):
        run("Missing", "local", config)


def test_main(executed):
    assert main(["--runtime", "PowerPlantMcp", "--mode", "local"]) == 0
    assert executed[0][1]["FASTMCP_PORT"] == "18731"


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_run",
        preview=False,
    )
