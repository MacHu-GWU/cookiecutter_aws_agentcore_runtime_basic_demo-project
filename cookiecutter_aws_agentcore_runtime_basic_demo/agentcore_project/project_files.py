# -*- coding: utf-8 -*-

"""
Generate the AgentCore CLI project files in ``agentcore/`` from the config:
``agentcore.json`` (the runtimes; committed) and ``aws-targets.json`` (one
deployment target per environment; git-ignored, it holds account IDs).

The config is the source of truth; never edit these files by hand.
"""

from __future__ import annotations

import json
import dataclasses
from pathlib import Path

from ..env import EnvNameEnum
from ..config.api import Config

#: The Python of every runtime; the dev Python, ``[tools] python`` in ``mise.toml``.
RUNTIME_PYTHON = "3.12"

#: :data:`RUNTIME_PYTHON` as AgentCore names it in ``agentcore.json``.
RUNTIME_VERSION = "PYTHON_" + RUNTIME_PYTHON.replace(".", "_")


@dataclasses.dataclass
class RuntimeSpec:
    """
    One AgentCore Runtime of the project.
    """

    # fmt: off
    name: str = dataclasses.field()  #: Name in ``agentcore.json``, from ``agentcore_runtime_name_*`` of the config.
    module: str = dataclasses.field()  #: Module with a ``main()`` that runs the server, relative to the package, such as ``runtimes.site_agent``.
    protocol: str = dataclasses.field()  #: ``MCP`` for an MCP server, ``HTTP`` for an agent.
    # fmt: on


def get_runtime_specs(config: Config) -> list[RuntimeSpec]:
    """
    Every runtime of the project. To add a runtime, add a name to the config and a line here.
    """
    return [
        RuntimeSpec(
            name=config.agentcore_runtime_name_power_plant_mcp,
            module="runtimes.power_plant_mcp",
            protocol="MCP",
        ),
        RuntimeSpec(
            name=config.agentcore_runtime_name_site_agent,
            module="runtimes.site_agent",
            protocol="HTTP",
        ),
    ]


def build_agentcore_json(config: Config) -> dict:
    """
    The content of ``agentcore/agentcore.json``. The same for every environment:
    it uses only config values shared by all of them.
    """
    runtimes = []
    for spec in get_runtime_specs(config):
        runtime = {
            "name": spec.name,
            "build": "CodeZip",
            "entrypoint": "main.py",
            "codeLocation": f"app/{spec.name}",
            "runtimeVersion": RUNTIME_VERSION,
            "protocol": spec.protocol,
        }
        runtimes.append(runtime)
    return {
        "name": config.agentcore_project_name,
        "version": 2,
        "managedBy": "CDK",
        "runtimes": runtimes,
    }


def build_aws_targets_json(configs: list[Config]) -> list[dict]:
    """
    The content of ``agentcore/aws-targets.json``: one target per config, named after its environment.
    """
    targets = []
    for config in configs:
        target = {
            "name": config.agentcore_target_name,
            "description": f"The {config.env_name} environment",
            "account": config.aws_account_id,
            "region": config.aws_region,
        }
        targets.append(target)
    return targets


def load_all_configs() -> list[Config]:
    """
    The config of every environment, read from the local config files.
    """
    configs = []
    for env_name in EnvNameEnum:
        config = Config.load_from_local_config_file(env_name=env_name.value)
        configs.append(config)
    return configs


def write_json(path: Path, data: dict | list) -> bool:
    """
    Write ``data`` as indented JSON; returns ``True`` if the file changed.
    """
    content = json.dumps(data, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True
