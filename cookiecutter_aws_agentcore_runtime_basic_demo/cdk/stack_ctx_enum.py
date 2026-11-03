# -*- coding: utf-8 -*-

"""
Layer 1 of the cdk_mate two-layer pattern: one :class:`~cdk_mate.stack_ctx.StackCtx`
per stack of the current environment, with its construct ID, stack name, account,
region, and session (``one.bsm``). Building one creates no CDK construct and makes
no AWS call. Layer 2, :mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_enum`, has an entry
of the same name per stack; ``mise run gen-env-tasks`` reads the entry names.
"""

from __future__ import annotations

import typing as T
import dataclasses
from functools import cached_property

from cdk_mate.api import StackCtx

if T.TYPE_CHECKING:  # pragma: no cover
    from ..one.api import One


def list_entry_names(klass: type) -> list[str]:
    """
    The names of the cached properties of ``klass``, in definition order.
    Reads only the class, so it builds nothing.
    """
    return [
        name
        for name, attr in klass.__dict__.items()
        if isinstance(attr, cached_property)
    ]


@dataclasses.dataclass
class StackCtxEnum:
    """
    One entry per stack, named like the stack (``alerts``), in creation order:
    a stack comes after the stacks it depends on.
    """

    # fmt: off
    one: One = dataclasses.field()  #: The project singleton, for ``config`` and ``bsm``.
    # fmt: on

    def _new(self, stack_name: str) -> StackCtx:
        """
        The construct ID is the stack name itself, which already says the
        environment. The account and region come from the config, not from an
        STS call as in :meth:`cdk_mate.stack_ctx.StackCtx.new`.
        """
        return StackCtx(
            construct_id=stack_name,
            stack_name=stack_name,
            aws_account_id=self.one.config.aws_account_id,
            aws_region=self.one.config.aws_region,
            bsm=self.one.bsm,
        )

    @cached_property
    def alerts(self) -> StackCtx:
        return self._new(self.one.config.cft_stack_name_alerts)

    @cached_property
    def publisher(self) -> StackCtx:
        return self._new(self.one.config.cft_stack_name_publisher)

    @cached_property
    def agentcore_deps(self) -> StackCtx:
        return self._new(self.one.config.cft_stack_name_agentcore_deps)

    def get(self, stack: str) -> StackCtx:
        """
        The entry of a stack given by name, such as ``get("alerts")``.

        :raises AttributeError: there is no such entry.
        """
        return getattr(self, stack)

    def get_all(self) -> list[StackCtx]:
        """
        Every entry, in creation order; loop over this instead of naming each stack.
        """
        return [self.get(name) for name in list_entry_names(type(self))]
