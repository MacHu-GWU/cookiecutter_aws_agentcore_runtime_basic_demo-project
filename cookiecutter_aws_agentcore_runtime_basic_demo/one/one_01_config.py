# -*- coding: utf-8 -*-

"""
The :attr:`~cookiecutter_aws_agentcore_runtime_basic_demo.one.one_01_config.OneConfigMixin.config` part of ``one``.
"""

from __future__ import annotations

import typing as T
from functools import cached_property

from ..config.api import Config

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One


class OneConfigMixin:
    """
    Builds the project :class:`~cookiecutter_aws_agentcore_runtime_basic_demo.config.config_00_main.Config`.
    """

    @cached_property
    def config(self: One) -> Config:
        """
        The configuration of the current environment and runtime, loaded once on first access.

        See :meth:`~cookiecutter_aws_agentcore_runtime_basic_demo.config.config_00_main.Config.load`.
        """
        return Config.load(
            env_name=self.env.current_env_name,
            runtime_name=self.runtime.current_runtime_name(),
        )
