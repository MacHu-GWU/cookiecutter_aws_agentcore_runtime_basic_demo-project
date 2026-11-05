# -*- coding: utf-8 -*-

"""
The check of ``one`` before ``agentcore deploy``: what the AgentCore runtimes
depend on but do not deploy themselves exists. Deploying the config itself is
:mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.one.one_06_config_deploy`.
"""

from __future__ import annotations

import typing as T

import simple_aws_ssm_parameter_store.api as simple_aws_ssm_parameter_store

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_ssm.client import SSMClient
    from mypy_boto3_iam.client import IAMClient
    from ..config.api import Config
    from .one_00_main import One


def check_agentcore_deps(
    config: Config,
    iam_client: IAMClient,
    ssm_client: SSMClient,
) -> bool:
    """
    Check that what the AgentCore runtimes depend on exists, before
    ``agentcore deploy``: the runtime policy of the ``agentcore_deps`` stack,
    which ``agentcore.json`` refers to (the deploy fails without it), and the
    config parameter, which the runtimes read at startup (they fail without it).
    Prints each result, and the task to run for what is missing.

    :param iam_client: an IAM client of the account of ``config``.
    :param ssm_client: an SSM client of the account of ``config``.

    :returns: ``True`` if both exist.
    """
    ok = True
    try:
        iam_client.get_policy(PolicyArn=config.iam_policy_arn_agentcore_runtime)
        print(f"The policy {config.iam_policy_name_agentcore_runtime} exists")
    except iam_client.exceptions.NoSuchEntityException:
        print(
            f"The policy {config.iam_policy_name_agentcore_runtime} does not exist: "
            f"deploy the stack {config.cft_stack_name_agentcore_deps} first, "
            f"with `mise run cdk-up-{config.env_name}-agentcore-deps-stack`"
        )
        ok = False
    parameter = simple_aws_ssm_parameter_store.get_parameter(
        ssm_client, config.ssm_param_name_config
    )
    if parameter is None:
        print(
            f"The config parameter {config.ssm_param_name_config} does not exist: "
            f"deploy it first, with `mise run config-deploy-{config.env_name}`"
        )
        ok = False
    else:
        print(f"The config parameter {config.ssm_param_name_config} exists")
    return ok


class OneDevOpsMixin:
    """
    The checks before ``agentcore deploy``.
    """

    def check_agentcore_deps(self: One) -> bool:
        """
        :func:`check_agentcore_deps` for the current environment.
        """
        return check_agentcore_deps(
            config=self.config,
            iam_client=self.iam_client,
            ssm_client=self.ssm_client,
        )
