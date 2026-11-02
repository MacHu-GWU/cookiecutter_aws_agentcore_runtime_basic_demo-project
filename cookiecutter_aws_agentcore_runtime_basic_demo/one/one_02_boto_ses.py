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

    @cached_property
    def bsm(self: One) -> BotoSesManager:  # pragma: no cover
        """
        The boto session of the current environment, in the region of its config;
        creating it makes no AWS call.

        On the local runtime it uses the profile ``AWS_PROFILE_FOR_<ENV>`` of the
        current environment when that is set. Otherwise it follows the standard
        credential chain, as a CI runner would.
        """
        region_name = self.config.aws_region
        if self.runtime.current_runtime_name() == RuntimeNameEnum.local.value:
            env_var = get_aws_profile_env_var(self.env.current_env_name)
            profile_name = os.environ.get(env_var, "")
            if profile_name:
                return BotoSesManager(
                    profile_name=profile_name, region_name=region_name
                )
        return BotoSesManager(region_name=region_name)

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
