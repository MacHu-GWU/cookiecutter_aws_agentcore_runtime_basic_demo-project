# -*- coding: utf-8 -*-

"""
Layer 2 of the cdk_mate two-layer pattern: one CDK stack per entry of
:class:`~cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_ctx_enum.StackCtxEnum`, same name,
written out by hand:

- **Arguments by name,** so a new ``__init__`` argument breaks every entry that
  does not pass it.
- **Dependencies are attribute access:** ``publisher`` passes
  ``self.alerts.alert_topic``, so CDK exports it from the alerts stack, imports it
  in the publisher stack, and deploys alerts first.
- **One instance per stack:** a cached property is built once; the same construct
  ID twice in one ``cdk.App`` is an error.
"""

from __future__ import annotations

import typing as T
import dataclasses
from functools import cached_property

import aws_cdk as cdk

from .stack_ctx_enum import list_entry_names
from .stacks.alerts_stack import AlertsStack
from .stacks.publisher_stack.stack import PublisherStack
from .stacks.agentcore_deps_stack import AgentCoreDepsStack

if T.TYPE_CHECKING:  # pragma: no cover
    from ..one.api import One


@dataclasses.dataclass
class StackEnum:
    """
    The stacks of the current environment, created in :attr:`app` on first access.
    """

    # fmt: off
    app: cdk.App = dataclasses.field()  #: The CDK app that owns every stack.
    one: One = dataclasses.field()  #: The project singleton, for ``config`` and ``stack_ctx_enum``.
    # fmt: on

    @cached_property
    def alerts(self) -> AlertsStack:
        return AlertsStack(
            scope=self.app,
            **self.one.stack_ctx_enum.alerts.to_stack_kwargs(),
            config=self.one.config,
        )

    @cached_property
    def publisher(self) -> PublisherStack:
        return PublisherStack(
            scope=self.app,
            **self.one.stack_ctx_enum.publisher.to_stack_kwargs(),
            config=self.one.config,
            alert_topic=self.alerts.alert_topic,
        )

    @cached_property
    def agentcore_deps(self) -> AgentCoreDepsStack:
        return AgentCoreDepsStack(
            scope=self.app,
            **self.one.stack_ctx_enum.agentcore_deps.to_stack_kwargs(),
            config=self.one.config,
        )

    def get(self, stack: str) -> cdk.Stack:
        """
        Create (once) and return the stack given by name, such as ``get("alerts")``.

        :raises AttributeError: there is no such entry.
        """
        return getattr(self, stack)

    def get_all(self) -> list[cdk.Stack]:
        """
        Create every stack, in creation order, and return them; loop over this
        instead of naming each stack.
        """
        return [self.get(name) for name in list_entry_names(type(self))]

    def synth(self) -> None:
        """
        Create every stack, then synthesize the app into ``cdk.out``.
        """
        self.get_all()
        self.app.synth()
