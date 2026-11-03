# -*- coding: utf-8 -*-

"""
``mise run ac-gen``: write every generated file of the AgentCore CLI project.
"""

from __future__ import annotations

from ..paths import path_enum
from ..env import env
from ..config.api import Config
from .project_files import get_runtime_specs
from .project_files import build_agentcore_json
from .project_files import build_aws_targets_json
from .project_files import build_runtime_env_json
from .project_files import build_env_local
from .project_files import load_all_configs
from .project_files import write_json
from .project_files import write_text
from .runtime_dir import export_requirements
from .runtime_dir import assemble_runtime_dir


def generate_all(config: Config, configs: list[Config]) -> None:
    """
    Write ``agentcore/agentcore.json``, ``agentcore/aws-targets.json``,
    ``agentcore/runtime-env.json``, ``agentcore/.env.local``, and
    ``app/<Runtime>/`` of every runtime.

    :param config: the config of the current environment: shared values go to
        ``agentcore.json``, its own ones to ``.env.local`` for ``agentcore dev``.
    :param configs: the config of every environment, one deployment target each.
    """
    write_json(path_enum.path_agentcore_json, build_agentcore_json(config))
    write_json(path_enum.path_aws_targets_json, build_aws_targets_json(configs))
    write_json(path_enum.path_runtime_env_json, build_runtime_env_json(configs))
    write_text(path_enum.path_agentcore_env_local, build_env_local(config))
    requirements = export_requirements()
    for spec in get_runtime_specs(config):
        assemble_runtime_dir(
            dir_runtime=path_enum.dir_agentcore_app / spec.name,
            name=spec.name,
            module=spec.module,
            protocol=spec.protocol,
            requirements=requirements,
        )
        print(f"Assembled {path_enum.dir_agentcore_app / spec.name}")


def main():
    """
    Generate with the local config files of every environment; ``.env.local``
    is for the current one, ``ENV_NAME`` (default ``dev``).
    """
    configs = load_all_configs()
    by_env_name = {config.env_name: config for config in configs}
    generate_all(config=by_env_name[env.current_env_name], configs=configs)
