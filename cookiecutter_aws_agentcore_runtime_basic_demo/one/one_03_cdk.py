# -*- coding: utf-8 -*-

"""
The CDK part of ``one``: the two layers of the cdk_mate pattern, for the current
environment. The CDK modules are imported inside the properties, so importing
``one`` does not load ``aws_cdk``.
"""

from __future__ import annotations

import typing as T
from functools import cached_property

if T.TYPE_CHECKING:  # pragma: no cover
    from ..cdk.stack_ctx_enum import StackCtxEnum
    from ..cdk.stack_enum import StackEnum
    from .one_00_main import One


class OneCdkMixin:
    """
    Lazily built CDK stack contexts and stacks.
    """

    @cached_property
    def stack_ctx_enum(self: One) -> StackCtxEnum:
        """
        One ``cdk_mate.StackCtx`` per stack, such as ``one.stack_ctx_enum.alerts``.
        """
        from ..cdk.stack_ctx_enum import StackCtxEnum

        return StackCtxEnum(one=self)

    @cached_property
    def stack_enum(self: One) -> StackEnum:
        """
        One CDK stack per stack, in a new ``cdk.App``, such as ``one.stack_enum.alerts``.
        """
        import aws_cdk as cdk

        from ..cdk.stack_enum import StackEnum

        return StackEnum(app=cdk.App(), one=self)
