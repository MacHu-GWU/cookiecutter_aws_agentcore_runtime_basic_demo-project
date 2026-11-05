# -*- coding: utf-8 -*-

"""
A small client to call an agent runtime's HTTP server by hand, the way
AgentCore Runtime calls it: ``POST /invocations`` with a JSON payload, and the
runtime session ID in a header. ``mise run ac-local-<slug>-call`` uses it on a
local agent server, started with ``ac-local-<slug>`` or ``ac-dev-<slug>``.
"""

from __future__ import annotations

import os
import json
import argparse

import httpx

AGENT_URL_VAR = "AGENT_URL"
"""
The base URL of the agent server to call when ``--url`` is not given, such as
``AGENT_URL=http://localhost:18732``.
"""

SESSION_ID_HEADER = "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id"
"""
The header that carries the runtime session ID; AgentCore Runtime sets it from
``runtimeSessionId`` of ``InvokeAgentRuntime``.
"""


def invoke_agent(
    url: str,
    payload: dict,
    session_id: str | None = None,
    timeout: float = 300,
) -> dict:
    """
    Send ``payload`` to the agent server at the base URL ``url``, and return
    its JSON answer.

    :param session_id: the runtime session ID to send, if any.
    :param timeout: seconds to wait: an answer can take several model calls.

    :raises httpx.HTTPStatusError: the server answered with an error status.
    """
    headers = {}
    if session_id:
        headers[SESSION_ID_HEADER] = session_id
    response = httpx.post(
        f"{url.rstrip('/')}/invocations",
        json=payload,
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def main(args: list[str] | None = None) -> int:
    """
    ``agent_client --prompt <text> [--url <url>] [--session-id <id>]``: print
    the agent's answer. Exit 1 if the server answers with an error.
    """
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    url = os.environ.get(AGENT_URL_VAR)
    parser.add_argument(
        "--url",
        default=url,
        required=url is None,
        help=f"the base URL (default: ${AGENT_URL_VAR})",
    )
    parser.add_argument("--prompt", required=True, help="what to ask the agent")
    parser.add_argument(
        "--session-id",
        default=None,
        help="a runtime session ID, to continue a conversation",
    )
    parsed = parser.parse_args(args)
    print(f"Agent server: {parsed.url}")
    print(f"prompt: {parsed.prompt}")
    try:
        answer = invoke_agent(
            parsed.url,
            {"prompt": parsed.prompt},
            session_id=parsed.session_id,
        )
    except httpx.HTTPStatusError as e:
        print(f"error: {e}")
        return 1
    result = answer.get("result") if isinstance(answer, dict) else None
    if isinstance(result, str):
        print(result)
    else:  # pragma: no cover
        print(json.dumps(answer, indent=2))
    return 0
