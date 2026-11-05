# -*- coding: utf-8 -*-

"""
The AWS session part of ``one``: :attr:`~cookiecutter_aws_agentcore_runtime_basic_demo.one.one_02_boto_ses.OneBotoSesMixin.bsm`,
the boto session of the current environment, and the clients built from it.
The account and region are ``one.config.aws_account_id`` / ``one.config.aws_region``.
"""

from __future__ import annotations

import typing as T
import os
from functools import cached_property

import boto3
from boto_session_manager.api import BotoSesManager

from ..runtime import RuntimeNameEnum

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One


def get_aws_profile_env_var(env_name: str) -> str:
    """
    The environment variable that names the local AWS profile of an environment,
    such as ``AWS_PROFILE_FOR_DEV`` for ``dev``; mise loads it from ``.env``.
    """
    return f"AWS_PROFILE_FOR_{env_name.upper()}"


class OneBotoSesMixin:
    """
    Lazily built boto session and AWS clients.
    """

    def get_bsm_kwargs(self: One) -> dict:
        """
        The arguments of the boto session of the current environment:

        - Region: that of the config, except on the AgentCore runtimes, which
          read the config through this session: there it is ``AWS_REGION``, set
          by AgentCore and by ``agentcore dev``. botocore itself reads only
          ``AWS_DEFAULT_REGION``, so it is passed explicitly.
        - Credentials: on the local and ``agentcore_local`` runtimes, the profile
          ``AWS_PROFILE_FOR_<ENV>`` of the current environment when that is set.
          Otherwise the standard credential chain, as a CI runner or a deployed
          AgentCore runtime (its execution role) would.
        """
        runtime_name = self.runtime.current_runtime_name()
        kwargs = {}
        if runtime_name in (
            RuntimeNameEnum.agentcore.value,
            RuntimeNameEnum.agentcore_local.value,
        ):
            kwargs["region_name"] = os.environ.get("AWS_REGION")
        else:
            kwargs["region_name"] = self.config.aws_region
        if runtime_name in (
            RuntimeNameEnum.local.value,
            RuntimeNameEnum.agentcore_local.value,
        ):
            env_var = get_aws_profile_env_var(self.env.current_env_name)
            profile_name = os.environ.get(env_var, "")
            if profile_name:
                kwargs["profile_name"] = profile_name
        return kwargs

    @cached_property
    def bsm(self: One) -> BotoSesManager:
        """
        The boto session of the current environment, built once with
        :meth:`get_bsm_kwargs`; creating it makes no AWS call.
        """
        return BotoSesManager(**self.get_bsm_kwargs())

    def new_boto_ses(self: One) -> boto3.Session:
        """
        A new boto3 session of the current environment on every call, with the
        same region and credential rules as :attr:`bsm`, and credentials
        resolved now. An agent runtime builds its agent with one on its first
        invocation, so its credentials are those of the running session, never
        ones resolved before (an AgentCore microVM is restored from a snapshot).
        """
        return BotoSesManager(**self.get_bsm_kwargs()).boto_ses

    @cached_property
    def boto_ses(self: One) -> boto3.Session:  # pragma: no cover
        """
        The boto3 session of :attr:`bsm`.
        """
        return self.bsm.boto_ses

    @cached_property
    def cloudformation_client(self: One):  # pragma: no cover
        """
        A CloudFormation client from :attr:`boto_ses`.
        """
        return self.boto_ses.client("cloudformation")

    @cached_property
    def ssm_client(self: One):  # pragma: no cover
        """
        An SSM client from :attr:`boto_ses`.
        """
        return self.boto_ses.client("ssm")

    @cached_property
    def iam_client(self: One):  # pragma: no cover
        """
        An IAM client from :attr:`boto_ses`.
        """
        return self.boto_ses.client("iam")

    @cached_property
    def bedrock_agentcore_client(self: One):  # pragma: no cover
        """
        An AgentCore data plane client from :attr:`boto_ses`: invokes runtimes.
        """
        return self.boto_ses.client("bedrock-agentcore")

    @cached_property
    def bedrock_agentcore_control_client(self: One):  # pragma: no cover
        """
        An AgentCore control plane client from :attr:`boto_ses`: lists runtimes.
        """
        return self.boto_ses.client("bedrock-agentcore-control")
