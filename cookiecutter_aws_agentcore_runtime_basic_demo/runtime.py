# -*- coding: utf-8 -*-

"""
Runtime detection: where this code is running (a developer's machine or CI).

Some behavior differs by runtime. For example, locally the AWS credentials come
from a named profile, while in CI they come from environment variables or an
assumed role. Instead of checking ``os.environ`` in every module, code asks the
module-level :data:`runtime` singleton, so the detection rule lives in one place::

    from .runtime import runtime

    if runtime.current_runtime_name() == "ci":
        ...

Importing this module has no side effect; the runtime is worked out when asked.
"""

from __future__ import annotations

import os
import enum


class RuntimeNameEnum(enum.Enum):
    """
    Every runtime this project's code can run in.
    """

    #: A developer's machine.
    local = "local"
    #: A CI/CD runner, such as GitHub Actions.
    ci = "ci"


class Runtime:
    """
    Detects the current runtime.

    Use the module-level :data:`runtime` singleton instead of creating new instances.
    """

    def get_current_runtime_name(self) -> RuntimeNameEnum:
        """
        Work out the current runtime.

        The ``CI`` environment variable counts as the signal, because GitHub Actions
        and most other CI services set it on every runner.
        """
        if "CI" in os.environ:
            return RuntimeNameEnum.ci
        else:
            return RuntimeNameEnum.local

    def current_runtime_name(self) -> str:
        """
        The current runtime name, such as ``"local"``.
        """
        return self.get_current_runtime_name().value


runtime = Runtime()
"""
The single :class:`Runtime` instance of this project.
"""
