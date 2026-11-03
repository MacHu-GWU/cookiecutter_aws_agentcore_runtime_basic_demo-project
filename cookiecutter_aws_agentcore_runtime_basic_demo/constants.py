# -*- coding: utf-8 -*-

"""
Fixed names shared by the dev machine and the AgentCore runtimes.
"""

IS_AGENTCORE_RUNTIME_VAR = "IS_AGENTCORE_RUNTIME"
"""
Set to ``"true"`` on every AgentCore runtime through ``envVars`` in
``agentcore/agentcore.json``. AgentCore documents no variable of its own that
tells a runtime it runs there, so the project sets this one. ``agentcore dev``
sets it too, as it applies ``envVars``.
"""

AGENTCORE_DEV_VAR = "LOCAL_DEV"
"""
Set to ``"1"`` by ``agentcore dev`` (AgentCore CLI 1.0.1) on the server it runs,
and absent on a deployed runtime. Undocumented CLI behavior: check it again
after upgrading ``@aws/agentcore``.
"""

CONFIG_SSM_PARAM_NAME_VAR = "CONFIG_SSM_PARAM_NAME"
"""
The SSM parameter that holds the config, on an AgentCore runtime: set through
``envVars`` in ``agentcore/agentcore.json``, which ``mise run ac-gen`` writes for
one environment, so both a deployed runtime and ``agentcore dev`` get it.
"""
