# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.registry import (
    RUNTIME_VERSION,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.registry import (
    RuntimeProtocolEnum,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.registry import (
    get_runtime_specs,
)

import importlib

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import PACKAGE_NAME
from cookiecutter_aws_agentcore_runtime_basic_demo.paths import path_enum
from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config


def test_runtime_version():
    assert RUNTIME_VERSION == "PYTHON_3_12"


def test_get_runtime_specs(config: Config):
    specs = get_runtime_specs(config)
    assert [spec.name for spec in specs] == ["PowerPlantMcp", "SiteAgent"]
    assert [spec.protocol for spec in specs] == [
        RuntimeProtocolEnum.MCP,
        RuntimeProtocolEnum.HTTP,
    ]

    assert [spec.slug for spec in specs] == ["power-plant-mcp", "site-agent"]


def test_sample_payloads(config: Config):
    """An agent gets a prompt; an MCP server a whole JSON-RPC request."""
    for spec in get_runtime_specs(config):
        if spec.protocol == RuntimeProtocolEnum.HTTP:
            assert isinstance(spec.sample_payload["prompt"], str)
        else:
            assert spec.sample_payload["jsonrpc"] == "2.0"
            assert spec.sample_payload["method"] == "tools/call"


def test_every_runtime_module_has_its_entry_points(config: Config):
    """Each module has main(), and app for HTTP: what the generated main.py imports."""
    for spec in get_runtime_specs(config):
        module = importlib.import_module(f"{PACKAGE_NAME}.{spec.module}")
        assert callable(module.main)
        if spec.protocol == RuntimeProtocolEnum.HTTP:
            assert module.app is not None


def test_local_ports_and_mcp_runtimes(config: Config):
    """
    Every runtime has its own local port, below the ephemeral range; an agent
    calls only MCP runtimes of the registry, each bound to it in cdk-stack.ts.
    """
    specs = get_runtime_specs(config)
    ports = [spec.local_port for spec in specs]
    assert len(set(ports)) == len(ports)
    assert all(1024 <= port < 32768 for port in ports)
    protocols = {spec.name: spec.protocol for spec in specs}
    content = path_enum.path_agentcore_cdk_stack_ts.read_text(encoding="utf-8")
    for spec in specs:
        if spec.protocol == RuntimeProtocolEnum.MCP:
            assert spec.mcp_runtimes == []
        for mcp_name in spec.mcp_runtimes:
            assert protocols[mcp_name] == RuntimeProtocolEnum.MCP
            line = (
                f"this.application.runtime('{mcp_name}')"
                f".bind(this.application.runtime('{spec.name}'));"
            )
            assert line in content


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.registry",
        preview=False,
    )
