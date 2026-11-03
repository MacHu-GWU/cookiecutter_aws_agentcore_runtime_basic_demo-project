# -*- coding: utf-8 -*-

"""
The top-level configuration model.

:class:`Config` holds every project-level setting the stacks and scripts need.
Resource names are not written here but derived in ``config_01_name.py``.

To add a group of related settings, put them in a new numbered module
(``config_01_xxx.py``, ``config_02_xxx.py``, ...) as a mixin or a nested model,
then add it to :class:`Config` here. The number gives the reading order: lower
modules are more foundational.

**Where the values come from:** on a developer's machine, ``config/*.json5`` files at
the repo root, read by :meth:`Config.load_from_local_config_file`. On an AgentCore
runtime (deployed, or run by ``agentcore dev``), the SSM parameter that
``mise run config-deploy-<env>`` writes, read by :meth:`Config.load_from_ssm`.
See :meth:`Config.load`.
"""

from __future__ import annotations

import typing as T
import os
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field
from simple_aws_ssm_parameter_store.api import get_parameter

from ..paths import path_enum
from ..constants import CONFIG_SSM_PARAM_NAME_VAR
from ..runtime import RuntimeNameEnum
from .config_01_name import ConfigNameMixin

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_ssm.client import SSMClient


class Config(
    BaseModel,
    ConfigNameMixin,
):
    """
    Project-wide settings of one environment, validated on load.

    Every resource name is derived from these values in
    :class:`~cookiecutter_aws_agentcore_runtime_basic_demo.config.config_01_name.ConfigNameMixin`.
    """

    # fmt: off
    project_name: str = Field()  #: Project name in snake_case or slug-case, such as ``my_project``.
    env_name: str = Field()  #: The environment these values are for, such as ``dev``.
    aws_account_id: str = Field()  #: The AWS account this environment deploys to, kept in ``config-<env>-secret.json5``; the session must match it.
    aws_region: str = Field()  #: The AWS region this environment deploys to; the session must match it.
    log_level: str = Field()  #: Log level of this environment, such as ``DEBUG``; the alerts stack stores it in SSM.
    agentcore_project_name: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9]{0,22}$")  #: The AgentCore CLI project name, such as ``MyProject``: a letter, then letters and digits, at most 23 characters; it starts every AgentCore resource name.
    site_agent_model_id: str = Field()  #: The Bedrock model (or inference profile) ID of the SiteAgent, such as ``us.amazon.nova-2-lite-v1:0``.
    # fmt: on

    @classmethod
    def load_from_local_config_file(
        cls,
        env_name: str,
        dir_config: Path | None = None,
    ) -> Config:
        """
        Load the config of one environment from the json5 files in ``dir_config``.

        Four files are merged, a later one overriding the keys of an earlier one:
        ``config-shared.json5``, ``config-shared-secret.json5``,
        ``config-<env_name>.json5``, ``config-<env_name>-secret.json5``.
        The ``-secret`` files are git-ignored and may be missing; the others are required.
        ``config/example/`` shows the shape of every file.

        :param env_name: such as ``dev``, see :class:`~cookiecutter_aws_agentcore_runtime_basic_demo.env.EnvNameEnum`.
        :param dir_config: the folder of the config files; defaults to ``path_enum.dir_config``.
        """
        # json5 is not in the agentcore dependency group: runtimes read the config from SSM.
        import json5

        if dir_config is None:
            dir_config = path_enum.dir_config
        data = {}
        for name in ["shared", env_name]:
            path = dir_config / f"config-{name}.json5"
            data.update(json5.loads(path.read_text(encoding="utf-8")))
            path_secret = dir_config / f"config-{name}-secret.json5"
            if path_secret.exists():
                data.update(json5.loads(path_secret.read_text(encoding="utf-8")))
        data["env_name"] = env_name
        return cls(**data)

    @classmethod
    def load_from_ssm(
        cls,
        ssm_client: SSMClient,
        name: str,
    ) -> Config:
        """
        Load the config from the SSM parameter ``name``.

        :raises ValueError: the parameter does not exist; deploy it with
            ``mise run config-deploy-<env>``.
        """
        parameter = get_parameter(ssm_client, name, with_decryption=True)
        if parameter is None:
            raise ValueError(
                f"config SSM parameter {name!r} does not exist, "
                "deploy it with `mise run config-deploy-<env>`"
            )
        return cls.model_validate_json(parameter.value)

    @classmethod
    def load(
        cls,
        env_name: str,
        runtime_name: str,
        ssm_client: SSMClient | None = None,
    ) -> Config:
        """
        Load the config the way the current runtime supports:

        - ``local``: from the local config files of ``env_name``.
        - ``agentcore``, ``agentcore_local``: from the SSM parameter named by the
          :data:`~cookiecutter_aws_agentcore_runtime_basic_demo.constants.CONFIG_SSM_PARAM_NAME_VAR`
          environment variable. The packaged code cannot see ``config/``, and copying
          the config into ``app/`` would ship its secrets in the CodeZip.

        :param env_name: such as ``dev``.
        :param runtime_name: such as ``local``, see :class:`~cookiecutter_aws_agentcore_runtime_basic_demo.runtime.RuntimeNameEnum`.
        :param ssm_client: required on the AgentCore runtimes.

        :raises NotImplementedError: on any other runtime, such as CI.
        """
        if runtime_name == RuntimeNameEnum.local.value:
            return cls.load_from_local_config_file(env_name=env_name)
        elif runtime_name in (
            RuntimeNameEnum.agentcore.value,
            RuntimeNameEnum.agentcore_local.value,
        ):
            return cls.load_from_ssm(
                ssm_client=ssm_client,
                name=os.environ[CONFIG_SSM_PARAM_NAME_VAR],
            )
        else:
            raise NotImplementedError(
                f"loading config on runtime {runtime_name!r} is not supported, "
                "deploy from a local machine"
            )
