# -*- coding: utf-8 -*-

"""
What the ``SiteAgent`` is, in plain Python: its instructions and its own tools.

No agent framework is imported here, so this is tested like any business code.
The runtime module
:mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent` turns
it into a Strands agent, adds the model and the MCP tools, and serves it.
"""

from __future__ import annotations

from .weather import get_weather

#: The system prompt: what the agent is for, and how it answers.
SYSTEM_PROMPT = (
    "You help plan inspections of solar and wind power plant sites. "
    "Use the tools to look up sites, their assets, assigned technicians, "
    "and tomorrow's weather. Answer every part of the question briefly, "
    "and name the facts you used."
)

#: The agent's own tools, as plain functions: each one's docstring is its tool
#: description, its type hints its input schema. The tools of its MCP servers
#: come on top of these.
TOOLS = [
    get_weather,
]
