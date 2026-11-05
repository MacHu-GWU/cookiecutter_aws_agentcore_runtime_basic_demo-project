# -*- coding: utf-8 -*-

"""
``mise run ac-gen``: write every generated file of the AgentCore CLI project,
for the current environment (``ENV_NAME``, default ``dev``).
"""

from __future__ import annotations

from ..paths import path_enum
from ..env import env
from ..config.api import Config
from .registry import get_runtime_specs
from .project_files import build_agentcore_json
from .project_files import build_empty_agentcore_json
from .project_files import build_aws_targets_json
from .project_files import write_json
from .codezip import export_requirements
from .codezip import assemble_runtime_dir


def generate_all(config: Config) -> None:
    """
    Write ``agentcore/agentcore.json``, ``agentcore/aws-targets.json``, and
    ``app/<Runtime>/`` of every runtime, for the environment of ``config``.
    """
    write_json(path_enum.path_agentcore_json, build_agentcore_json(config))
    write_json(path_enum.path_aws_targets_json, build_aws_targets_json(config))
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
    print(f"Generated the AgentCore project files for {config.env_name!r}")


def generate_teardown(config: Config) -> None:
    """
    Write an ``agentcore/agentcore.json`` that declares nothing, and the
    ``agentcore/aws-targets.json`` of the environment of ``config``, for
    ``agentcore deploy --yes`` to destroy that target's stack. ``app/`` is left
    alone. Run :func:`generate_all` afterwards to get the real project back.
    """
    write_json(path_enum.path_agentcore_json, build_empty_agentcore_json(config))
    write_json(path_enum.path_aws_targets_json, build_aws_targets_json(config))
    print(f"Generated an empty AgentCore project for {config.env_name!r}")


def main():
    """
    Generate with the local config files of the current environment.
    """
    generate_all(Config.load_from_local_config_file(env_name=env.current_env_name))


def main_teardown():
    """
    :func:`generate_teardown` with the local config files of the current environment.
    """
    generate_teardown(Config.load_from_local_config_file(env_name=env.current_env_name))
