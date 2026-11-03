# -*- coding: utf-8 -*-

"""
Runtime detection: where this code is running (a developer's machine, CI, a
deployed AgentCore runtime, or ``agentcore dev``).

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

from .constants import IS_AGENTCORE_RUNTIME_VAR
from .constants import AGENTCORE_DEV_VAR


class RuntimeNameEnum(enum.Enum):
    """
    Every runtime this project's code can run in.
    """

    #: A developer's machine.
    local = "local"
    #: A CI/CD runner, such as GitHub Actions.
    ci = "ci"
    #: A deployed AgentCore runtime.
    agentcore = "agentcore"
    #: The packaged runtime code in ``app/<Runtime>/``, run by ``agentcore dev`` on a developer's machine.
    agentcore_local = "agentcore_local"


class Runtime:
    """
    Detects the current runtime.

    Use the module-level :data:`runtime` singleton instead of creating new instances.
    """

    def get_current_runtime_name(self) -> RuntimeNameEnum:
        """
        Work out the current runtime, checking in this order:

        1. :data:`~cookiecutter_aws_agentcore_runtime_basic_demo.constants.IS_AGENTCORE_RUNTIME_VAR`
           is ``"true"``: ``agentcore_local`` if
           :data:`~cookiecutter_aws_agentcore_runtime_basic_demo.constants.AGENTCORE_DEV_VAR`
           is also set, otherwise ``agentcore``.
        2. ``CI`` is set: ``ci``. GitHub Actions and most other CI services set it on every runner.
        3. Otherwise ``local``, including the ``ac-local-*`` tasks, which run the
           package from the repo.
        """
        if os.environ.get(IS_AGENTCORE_RUNTIME_VAR) == "true":
            if AGENTCORE_DEV_VAR in os.environ:
                return RuntimeNameEnum.agentcore_local
            return RuntimeNameEnum.agentcore
        elif "CI" in os.environ:
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
