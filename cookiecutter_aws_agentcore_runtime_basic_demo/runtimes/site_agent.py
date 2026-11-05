# -*- coding: utf-8 -*-

"""
The ``SiteAgent`` runtime: the agent of
:mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.site_agent` as a
Strands agent, with the ``PowerPlantMcp`` tools, served by
:class:`BedrockAgentCoreApp` (``POST /invocations`` and ``GET /ping`` on port
8080, the AgentCore HTTP contract; the same server runs locally).

A thin layer: :func:`make_agent` assembles the agent from what it is given;
:func:`build_agent` gives it the dependencies of this process (the model ID of
the config, the boto session of ``one``, the MCP connection); :data:`agent`
keeps one agent per process (see
:class:`~cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.common.ProcessAgent`).
"""

from __future__ import annotations

import typing as T

import httpx
import pydantic
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from starlette.exceptions import HTTPException
from strands import Agent
from strands import tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

from ..one.api import one
from ..power_plant.site_agent import SYSTEM_PROMPT
from ..power_plant.site_agent import TOOLS
from ..power_plant.site_agent import SiteAgentRequest
from ..power_plant.site_agent import SiteAgentResponse
from .common import ProcessAgent
from .common import strip_thinking
from .common import print_config_source
from .mcp_connection import get_mcp_connection

if T.TYPE_CHECKING:  # pragma: no cover
    import boto3


def make_agent(
    model_id: str,
    boto_session: boto3.Session,
    mcp_url: str,
    mcp_auth: httpx.Auth | None = None,
) -> Agent:
    """
    The agent on the Bedrock model ``model_id``, called with the credentials and
    region of ``boto_session``, with its own tools and those of the MCP server at
    ``mcp_url``. ``agent.cleanup()`` closes the MCP connection.
    """
    return Agent(
        model=BedrockModel(model_id=model_id, boto_session=boto_session),
        system_prompt=SYSTEM_PROMPT,
        tools=[
            *[tool(func) for func in TOOLS],
            MCPClient(url=mcp_url, auth_provider=mcp_auth),
        ],
        callback_handler=None,
    )


def build_agent() -> Agent:
    """
    :func:`make_agent` with the dependencies of this process: ``site_agent_model_id``
    of the config, a new boto session of the environment (the local profile of
    the environment, or the runtime's execution role, resolved now, on the first
    invocation), and the ``PowerPlantMcp`` connection.
    """
    boto_session = one.new_boto_ses()
    mcp_url, mcp_auth = get_mcp_connection(
        runtime_name=one.config.agentcore_runtime_name_power_plant_mcp,
        boto_session=boto_session,
    )
    return make_agent(
        model_id=one.config.site_agent_model_id,
        boto_session=boto_session,
        mcp_url=mcp_url,
        mcp_auth=mcp_auth,
    )


#: The agent of this process, built by :func:`build_agent` on the first invocation.
agent = ProcessAgent(build_agent)

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    """
    Answer a :class:`SiteAgentRequest` with a :class:`SiteAgentResponse`, as
    JSON. A payload that does not validate is the caller's mistake: a 400 with
    pydantic's errors, before the agent is built or the model called
    (``BedrockAgentCoreApp`` answers any other exception with a 500).
    """
    try:
        request = SiteAgentRequest.model_validate(payload)
    except pydantic.ValidationError as e:
        errors = e.errors(include_url=False, include_context=False, include_input=False)
        raise HTTPException(status_code=400, detail=errors)
    answer = strip_thinking(agent(request.prompt))
    return SiteAgentResponse(result=answer).model_dump()


def main():
    """
    Load the config, then serve on port 8080, blocking until stopped.
    ``agentcore dev`` serves ``app`` with uvicorn instead, so there the config
    is loaded on the first request.
    """
    print_config_source()
    app.run()


if __name__ == "__main__":
    main()
