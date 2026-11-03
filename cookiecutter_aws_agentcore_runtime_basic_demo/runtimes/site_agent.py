# -*- coding: utf-8 -*-

"""
The ``SiteAgent`` runtime: a Strands agent that plans site inspections, using
the ``PowerPlantMcp`` tools plus its own ``get_weather`` tool.

AgentCore Runtime (protocol ``HTTP``) expects ``POST /invocations`` and
``GET /ping`` on port 8080; :class:`BedrockAgentCoreApp` provides both, and the
same server runs locally.
"""

from __future__ import annotations

import os
import re

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands import tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

from ..power_plant import weather

#: The LLM, a Bedrock cross-region inference profile (the cheapest that does tool use well).
MODEL_ID = "us.amazon.nova-lite-v1:0"

#: The PowerPlantMcp URL when both run locally (``mise run ac-local-mcp``).
LOCAL_MCP_URL = "http://localhost:8000/mcp"

#: Instructions for the agent.
SYSTEM_PROMPT = (
    "You help plan inspections of solar and wind power plant sites. "
    "Use the tools to look up sites, their assets, assigned technicians, "
    "and tomorrow's weather. Answer every part of the question briefly, "
    "and name the facts you used."
)

#: Nova models may wrap their reasoning in ``<thinking>`` tags, which is not part of the answer.
_THINKING_PATTERN = re.compile(r"<thinking>.*?</thinking>", re.DOTALL)

#: Nova models may wrap the answer itself in ``<response>`` tags.
_RESPONSE_TAG_PATTERN = re.compile(r"</?response>")

#: The agent's own tool; its description is the docstring of the business function.
get_weather = tool(weather.get_weather)


def strip_thinking(text: str) -> str:
    """
    Remove ``<thinking>...</thinking>`` blocks and ``<response>`` tags from a model answer.
    """
    text = _THINKING_PATTERN.sub("", text)
    text = _RESPONSE_TAG_PATTERN.sub("", text)
    return text.strip()


def get_mcp_url() -> str:
    """
    The URL of the PowerPlantMcp server: the ``MCP_URL`` env var, else :data:`LOCAL_MCP_URL`.
    """
    return os.environ.get("MCP_URL", LOCAL_MCP_URL)


def make_agent(mcp_url: str) -> Agent:
    """
    Create the agent, connected to the MCP server at ``mcp_url``.
    Call ``agent.cleanup()`` when done, to close the MCP connection.
    """
    return Agent(
        model=BedrockModel(model_id=MODEL_ID),
        system_prompt=SYSTEM_PROMPT,
        tools=[get_weather, MCPClient(url=mcp_url)],
        callback_handler=None,
    )


app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    """
    Answer ``payload["prompt"]``; returns ``{"result": <answer text>}``.
    """
    agent = make_agent(get_mcp_url())
    try:
        result = agent(payload["prompt"])
    finally:
        agent.cleanup()
    return {"result": strip_thinking(str(result))}


def main():
    """
    Run the agent's HTTP server on port 8080, blocking until stopped.
    """
    app.run()


if __name__ == "__main__":
    main()
