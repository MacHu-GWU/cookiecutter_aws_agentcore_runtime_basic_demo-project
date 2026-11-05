# -*- coding: utf-8 -*-

"""
Fixed names shared by the dev machine and the AgentCore runtimes.

The first group are the signals :mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.runtime`
reads to tell where the code runs; no other module reads them. Each one says who sets it.
"""

IS_AGENTCORE_RUNTIME_VAR = "IS_AGENTCORE_RUNTIME"
"""
Set to :data:`IS_AGENTCORE_RUNTIME_VALUE` on every AgentCore runtime through
``envVars`` in ``agentcore/agentcore.json``, which ``mise run ac-gen`` writes.
AgentCore documents no variable of its own that tells a runtime it runs there,
so the project sets this one. ``agentcore dev`` sets it too, as it applies
``envVars``; :data:`AGENTCORE_DEV_VAR` tells the two apart.
"""

IS_AGENTCORE_RUNTIME_VALUE = "true"
"""
The value of :data:`IS_AGENTCORE_RUNTIME_VAR` that means "an AgentCore runtime";
any other value does not.
"""

AGENTCORE_DEV_VAR = "LOCAL_DEV"
"""
Set (to ``"1"``) by ``agentcore dev`` (AgentCore CLI 1.0.1) on the server it
runs, and absent on a deployed runtime; only its presence counts. Undocumented
CLI behavior: check it again after upgrading ``@aws/agentcore``.
"""

CI_VAR = "CI"
"""
Set by GitHub Actions, and most other CI services, on every runner; only its
presence counts.
"""

CONFIG_SSM_PARAM_NAME_VAR = "CONFIG_SSM_PARAM_NAME"
"""
The SSM parameter that holds the config, on an AgentCore runtime: set through
``envVars`` in ``agentcore/agentcore.json``, which ``mise run ac-gen`` writes for
one environment, so both a deployed runtime and ``agentcore dev`` get it.
"""
