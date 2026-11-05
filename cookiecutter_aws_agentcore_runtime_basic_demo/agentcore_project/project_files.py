# -*- coding: utf-8 -*-

"""
Generate the AgentCore CLI project files in ``agentcore/`` from the config of
one environment, the one ``ac-gen`` runs for (``ENV_NAME``, default ``dev``),
and the runtime registry:

- ``agentcore.json``: the runtimes, with that environment's ``envVars`` and the
  ARN of its runtime policy (``additionalPolicies``).
- ``aws-targets.json``: that environment's deployment target only.

Both are git-ignored: the config is the source of truth, and the values differ
per environment (``ac-deploy-<env>`` regenerates them for ``<env>``). Never edit
them by hand. What the runtimes use but is not AgentCore, such as the runtime
policy, is deployed by the ``agentcore_deps`` CDK stack; these files only refer
to it by name.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..env import ENV_NAME_VAR
from ..constants import IS_AGENTCORE_RUNTIME_VAR
from ..constants import IS_AGENTCORE_RUNTIME_VALUE
from ..constants import CONFIG_SSM_PARAM_NAME_VAR
from ..config.api import Config
from .registry import RUNTIME_VERSION
from .registry import get_runtime_specs


def get_runtime_env_vars(config: Config) -> dict[str, str]:
    """
    The environment variables of every runtime: the runtime signal, the
    environment, and the config parameter to read.
    """
    return {
        IS_AGENTCORE_RUNTIME_VAR: IS_AGENTCORE_RUNTIME_VALUE,
        ENV_NAME_VAR: config.env_name,
        CONFIG_SSM_PARAM_NAME_VAR: config.ssm_param_name_config,
    }


def build_agentcore_json(config: Config) -> dict:
    """
    The content of ``agentcore/agentcore.json`` for the environment of ``config``.
    """
    env_vars = [
        {"name": name, "value": value}
        for name, value in get_runtime_env_vars(config).items()
    ]
    runtimes = []
    for spec in get_runtime_specs(config):
        runtime = {
            "name": spec.name,
            "build": "CodeZip",
            "entrypoint": "main.py",
            "codeLocation": f"app/{spec.name}",
            "runtimeVersion": RUNTIME_VERSION,
            "protocol": spec.protocol.value,
            "envVars": env_vars,
            "additionalPolicies": [config.iam_policy_arn_agentcore_runtime],
        }
        runtimes.append(runtime)
    return {
        **build_empty_agentcore_json(config),
        "runtimes": runtimes,
    }


def build_empty_agentcore_json(config: Config) -> dict:
    """
    The content of ``agentcore/agentcore.json`` that declares nothing, the shape
    ``agentcore create`` writes for an empty project. ``agentcore deploy --yes``
    of it destroys the target's stack and removes the target from
    ``agentcore/.cli/deployed-state.json``: the CLI's own teardown.
    """
    return {
        "name": config.agentcore_project_name,
        "version": 2,
        "managedBy": "CDK",
    }


def build_aws_targets_json(config: Config) -> list[dict]:
    """
    The content of ``agentcore/aws-targets.json``: the one target of the
    environment of ``config``, named after it.
    """
    return [
        {
            "name": config.agentcore_target_name,
            "description": f"The {config.env_name} environment",
            "account": config.aws_account_id,
            "region": config.aws_region,
        }
    ]


def write_json(path: Path, data: dict | list) -> bool:
    """
    Write ``data`` as indented JSON; returns ``True`` if the file changed.
    """
    content = json.dumps(data, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True
