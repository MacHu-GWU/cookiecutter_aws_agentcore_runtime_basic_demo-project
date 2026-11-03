# -*- coding: utf-8 -*-

"""
The deploy steps of ``one`` other than ``cdk deploy`` and ``agentcore deploy``:
the config in SSM Parameter Store, which the AgentCore runtimes read.
"""

from __future__ import annotations

import typing as T

import simple_aws_ssm_parameter_store.api as simple_aws_ssm_parameter_store

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_ssm.client import SSMClient
    from ..config.api import Config
    from .one_00_main import One


def deploy_config(
    config: Config,
    ssm_client: SSMClient,
) -> str:
    """
    Write the whole config as JSON to its SSM parameter,
    :attr:`~cookiecutter_aws_agentcore_runtime_basic_demo.config.config_01_name.ConfigNameMixin.ssm_param_name_config`,
    a ``SecureString``, only when the parameter is missing or differs.

    :param ssm_client: an SSM client of the account of ``config``.

    :returns: ``"created"``, ``"updated"``, or ``"unchanged"``.
    """
    ssm = simple_aws_ssm_parameter_store
    value = config.model_dump_json()
    before, after = ssm.put_parameter_if_changed(
        ssm_client=ssm_client,
        name=config.ssm_param_name_config,
        value=value,
        type=ssm.ParameterType.SECURE_STRING,
        tier=ssm.ParameterTier.INTELLIGENT_TIERING,
    )
    if before is None:
        status = "created"
        detail = f"version {after.version}"
    elif after is None:
        status = "unchanged"
        detail = f"version {before.version}, nothing written"
    else:
        status = "updated"
        detail = f"version {before.version} -> {after.version}"
    print(
        f"Config of {config.env_name!r} {status} ({detail}, {len(value)} bytes): "
        f"SSM parameter {config.ssm_param_name_config}"
    )
    print(f"  {config.ssm_param_url_config}")
    return status


def delete_config(
    config: Config,
    ssm_client: SSMClient,
) -> bool:
    """
    Delete the SSM parameter of :func:`deploy_config`; neither ``cdk-down`` nor
    ``agentcore`` deletes it. The runtimes of this environment fail after this.
    A missing parameter is not an error.

    :param ssm_client: an SSM client of the account of ``config``.

    :returns: ``True`` if it was deleted, ``False`` if it did not exist.
    """
    deleted = simple_aws_ssm_parameter_store.delete_parameter(
        ssm_client=ssm_client,
        name=config.ssm_param_name_config,
    )
    status = "deleted" if deleted else "not found, nothing deleted"
    print(
        f"Config of {config.env_name!r} {status}: "
        f"SSM parameter {config.ssm_param_name_config}"
    )
    print(f"  {config.ssm_param_url_config}")
    return deleted


class OneDevOpsMixin:
    """
    Config deployment.
    """

    def deploy_config(self: One) -> str:
        """
        :func:`deploy_config` for the current environment.
        """
        return deploy_config(config=self.config, ssm_client=self.ssm_client)

    def delete_config(self: One) -> bool:
        """
        :func:`delete_config` for the current environment.
        """
        return delete_config(config=self.config, ssm_client=self.ssm_client)
