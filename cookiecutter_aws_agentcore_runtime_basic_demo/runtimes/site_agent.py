# -*- coding: utf-8 -*-

"""
The ``SiteAgent`` runtime: a Strands agent that plans site inspections, using
the ``PowerPlantMcp`` tools plus its own ``get_weather`` tool.

AgentCore Runtime (protocol ``HTTP``) expects ``POST /invocations`` and
``GET /ping`` on port 8080; :class:`BedrockAgentCoreApp` provides both, and the
same server runs locally.

**One agent per process.** AgentCore gives each runtime session its own microVM
and process, so the agent built on the first invocation serves the whole session:
its MCP connection, and so its MCP session, stays open (the PowerPlantMcp microVM
stays warm), and it remembers the earlier turns of the conversation. Callers
continue a conversation by sending the same runtime session ID.
"""

from __future__ import annotations

import os
import re
import threading
import contextlib
import urllib.parse

import boto3
import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands import tool
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient

from ..one.api import one
from ..power_plant import weather

#: The PowerPlantMcp URL when nothing else is set: ``agentcore dev`` without ``--port``.
#: The ``ac-local-*`` and ``ac-dev-*`` mise tasks set ``MCP_URL`` to their own port.
LOCAL_MCP_URL = "http://localhost:8000/mcp"

#: Set on the deployed SiteAgent by ``runtime('PowerPlantMcp').bind(...)`` in ``cdk-stack.ts``.
MCP_ARN_ENV_VAR = "AGENTCORE_RUNTIME_POWERPLANTMCP_ARN"

#: Instructions for the agent.
SYSTEM_PROMPT = (
    "You help plan inspections of solar and wind power plant sites. "
    "Use the tools to look up sites, their assets, assigned technicians, "
    "and tomorrow's weather. Answer every part of the question briefly, "
    "and name the facts you used."
)

#: Some models (such as Nova) wrap their reasoning in ``<thinking>`` tags, which is not part of the answer.
_THINKING_PATTERN = re.compile(r"<thinking>.*?</thinking>", re.DOTALL)

#: Some models (such as Nova) wrap the answer itself in ``<response>`` tags.
_RESPONSE_TAG_PATTERN = re.compile(r"</?response>")

#: The agent's own tool; its description is the docstring of the business function.
get_weather = tool(weather.get_weather)


def print_config_source():
    """
    Load the config, and print where it came from; a runtime that cannot read
    its config fails here, at startup.
    """
    print(
        f"Loaded the config of {one.config.env_name!r} "
        f"on runtime {one.runtime.current_runtime_name()!r}",
        flush=True,
    )


def strip_thinking(text: str) -> str:
    """
    Remove ``<thinking>...</thinking>`` blocks and ``<response>`` tags from a model answer.
    """
    text = _THINKING_PATTERN.sub("", text)
    text = _RESPONSE_TAG_PATTERN.sub("", text)
    return text.strip()


class AwsSigV4Auth(httpx.Auth):
    """
    Sign each HTTP request with SigV4 for ``bedrock-agentcore``, using the
    default AWS credentials (the runtime's execution role when deployed).
    """

    requires_request_body = True

    def __init__(self, region: str):
        self.region = region
        self.credentials = boto3.Session().get_credentials()

    def auth_flow(self, request: httpx.Request):
        aws_request = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers={"host": request.url.host},
        )
        signer = SigV4Auth(
            self.credentials.get_frozen_credentials(),
            "bedrock-agentcore",
            self.region,
        )
        signer.add_auth(aws_request)
        request.headers.update(dict(aws_request.headers))
        yield request


def get_runtime_mcp_url(runtime_arn: str) -> str:
    """
    The MCP URL of a deployed MCP runtime, from its ARN.
    """
    region = runtime_arn.split(":")[3]
    quoted_arn = urllib.parse.quote(runtime_arn, safe="")
    return (
        f"https://bedrock-agentcore.{region}.amazonaws.com"
        f"/runtimes/{quoted_arn}/invocations?qualifier=DEFAULT"
    )


def get_mcp_connection() -> tuple[str, httpx.Auth | None]:
    """
    Where to reach PowerPlantMcp, as ``(url, auth)``:

    1. the ``MCP_URL`` env var, no auth;
    2. else the deployed runtime in :data:`MCP_ARN_ENV_VAR`, signed with SigV4;
    3. else :data:`LOCAL_MCP_URL`, no auth.
    """
    if "MCP_URL" in os.environ:
        return os.environ["MCP_URL"], None
    if MCP_ARN_ENV_VAR in os.environ:
        runtime_arn = os.environ[MCP_ARN_ENV_VAR]
        region = runtime_arn.split(":")[3]
        return get_runtime_mcp_url(runtime_arn), AwsSigV4Auth(region)
    return LOCAL_MCP_URL, None


def make_agent(
    model_id: str,
    mcp_url: str,
    mcp_auth: httpx.Auth | None = None,
) -> Agent:
    """
    Create the agent on the Bedrock model ``model_id``, connected to the MCP
    server at ``mcp_url``. ``agent.cleanup()`` closes the MCP connection.
    """
    return Agent(
        model=BedrockModel(model_id=model_id),
        system_prompt=SYSTEM_PROMPT,
        tools=[get_weather, MCPClient(url=mcp_url, auth_provider=mcp_auth)],
        callback_handler=None,
    )


#: The agent of this process, built by :func:`get_agent` on the first invocation.
_agent: Agent | None = None

#: One invocation at a time: a Strands agent cannot run two calls at once, and
#: the requests of one session are one conversation.
_agent_lock = threading.Lock()


def get_agent() -> Agent:
    """
    The agent of this process, built on first use with ``site_agent_model_id``
    of the config and the PowerPlantMcp connection. Credentials and the SigV4
    signer are made here, on the first invocation, never at import time.
    """
    global _agent
    if _agent is None:
        _agent = make_agent(one.config.site_agent_model_id, *get_mcp_connection())
    return _agent


def reset_agent() -> None:
    """
    Close and drop the agent of this process, so the next invocation builds a
    new one with a new MCP connection. A failing cleanup is ignored: the agent
    is dropped anyway.
    """
    global _agent
    agent, _agent = _agent, None
    if agent is not None:
        with contextlib.suppress(Exception):
            agent.cleanup()


app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    """
    Answer ``payload["prompt"]``; returns ``{"result": <answer text>}``.

    Uses the agent of this process (:func:`get_agent`). If the call fails, for
    example because the MCP connection broke, the agent is dropped and the next
    invocation starts over with a new one.
    """
    with _agent_lock:
        agent = get_agent()
        try:
            result = agent(payload["prompt"])
        except Exception:
            reset_agent()
            raise
    return {"result": strip_thinking(str(result))}


def main():
    """
    Load the config, then run the agent's HTTP server on port 8080, blocking
    until stopped. ``agentcore dev`` serves ``app`` with uvicorn instead, so
    there the config is loaded on the first request.
    """
    print_config_source()
    app.run()


if __name__ == "__main__":
    main()
