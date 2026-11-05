# -*- coding: utf-8 -*-

"""
Runtime detection: where this code is running.

The same code runs in four places:

- ``local``: a developer's machine, running the package from the repo (tests,
  scripts, the ``ac-local-*`` servers).
- ``agentcore_local``: the packaged copy in ``app/<Runtime>/``, run by
  ``agentcore dev`` on a developer's machine to simulate AgentCore.
- ``ci``: a CI/CD runner, such as GitHub Actions.
- ``agentcore``: a deployed AgentCore runtime.

Some behavior differs by runtime: where the config comes from, which AWS
credentials and region to use. Instead of checking ``os.environ`` in every
module, code asks the module-level :data:`runtime` singleton, so the detection
rule lives in one place::

    from .runtime import runtime
    from .runtime import RuntimeNameEnum

    if runtime.current_runtime_name() == RuntimeNameEnum.agentcore.value:
        ...

The hard part is telling ``agentcore_local`` from ``agentcore``: both run the
same packaged code with the same ``envVars``. The signals, and who sets each,
are in :mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.constants`.

Importing this module has no side effect; the runtime is worked out when asked.
"""

from __future__ import annotations

import os
import enum

from .constants import IS_AGENTCORE_RUNTIME_VAR
from .constants import IS_AGENTCORE_RUNTIME_VALUE
from .constants import AGENTCORE_DEV_VAR
from .constants import CI_VAR


class RuntimeNameEnum(enum.Enum):
    """
    Every runtime this project's code can run in.
    """

    #: A developer's machine, running the package from the repo.
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
           is :data:`~cookiecutter_aws_agentcore_runtime_basic_demo.constants.IS_AGENTCORE_RUNTIME_VALUE`:
           ``agentcore_local`` if
           :data:`~cookiecutter_aws_agentcore_runtime_basic_demo.constants.AGENTCORE_DEV_VAR`
           is also set, otherwise ``agentcore``. It comes first, so an AgentCore
           runtime is never taken for another one.
        2. :data:`~cookiecutter_aws_agentcore_runtime_basic_demo.constants.CI_VAR` is set: ``ci``.
        3. Otherwise ``local``.
        """
        if os.environ.get(IS_AGENTCORE_RUNTIME_VAR) == IS_AGENTCORE_RUNTIME_VALUE:
            if AGENTCORE_DEV_VAR in os.environ:
                return RuntimeNameEnum.agentcore_local
            return RuntimeNameEnum.agentcore
        elif CI_VAR in os.environ:
            return RuntimeNameEnum.ci
        else:
            return RuntimeNameEnum.local

    def current_runtime_name(self) -> str:
        """
        The current runtime name, such as ``"local"``: the value of
        :meth:`get_current_runtime_name`, worked out again on every call.
        """
        return self.get_current_runtime_name().value


runtime = Runtime()
"""
The single :class:`Runtime` instance of this project.
"""
