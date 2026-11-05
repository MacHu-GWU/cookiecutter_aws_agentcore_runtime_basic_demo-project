# -*- coding: utf-8 -*-

"""
A small MCP client to call an MCP runtime: list its tools, and call one with
JSON arguments, over streamable HTTP. ``mise run ac-local-<slug>-call`` uses it on
a local MCP server, started with ``ac-local-<slug>`` or ``ac-dev-<slug>``; with the SigV4
auth of :func:`~cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client.get_deployed_mcp_connection`
it calls a deployed MCP runtime.
"""

from __future__ import annotations

import os
import json
import asyncio
import argparse
import contextlib

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from ..runtimes.common import LOCAL_MCP_URL

MCP_URL_VAR = "MCP_URL"
"""
The URL of the MCP server this client calls when ``--url`` is not given, such
as ``MCP_URL=http://localhost:18731/mcp``.
"""

DEFAULT_MCP_URL = LOCAL_MCP_URL
"""
The URL when neither ``--url`` nor :data:`MCP_URL_VAR` is given: a local server
on the default port, such as ``agentcore dev`` without ``--port``.
"""


#: Seconds to wait to connect and send, and to read an answer (a tool may be slow).
TIMEOUT = httpx.Timeout(30.0, read=300.0)


@contextlib.asynccontextmanager
async def _open_session(url: str, auth: httpx.Auth | None):
    async with httpx.AsyncClient(auth=auth, timeout=TIMEOUT) as http_client:
        async with streamable_http_client(url, http_client=http_client) as (
            read,
            write,
            _,
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session


async def _list_tools(url: str, auth: httpx.Auth | None) -> list[str]:
    async with _open_session(url, auth) as session:
        result = await session.list_tools()
        return [tool.name for tool in result.tools]


async def _call_tool(url: str, name: str, arguments: dict, auth: httpx.Auth | None):
    async with _open_session(url, auth) as session:
        return await session.call_tool(name, arguments)


def list_tools(url: str, auth: httpx.Auth | None = None) -> list[str]:
    """
    The names of the tools of the MCP server at ``url``, in the server's order.

    :param auth: signs each request, such as the SigV4 auth of a deployed MCP
        runtime; ``None`` for a local server.
    """
    return asyncio.run(_list_tools(url, auth))


def call_tool(
    url: str,
    name: str,
    arguments: dict | None = None,
    auth: httpx.Auth | None = None,
):
    """
    Call the tool ``name`` of the MCP server at ``url``, and return its result
    as JSON data: the structured output (a list result is wrapped as
    ``{"result": [...]}``), else the JSON text.

    :param auth: as for :func:`list_tools`.

    :raises RuntimeError: the tool failed; the message is the server's.
    """
    # raised here, not inside the client's task group, which would wrap it
    result = asyncio.run(_call_tool(url, name, arguments or {}, auth))
    if result.isError:
        raise RuntimeError(result.content[0].text)
    if result.structuredContent is not None:
        return result.structuredContent
    return json.loads(result.content[0].text)  # pragma: no cover


def main(args: list[str] | None = None) -> int:
    """
    ``mcp_client --tool <name> --arguments <json> [--url <url>]``: print the
    tool names, then the tool's result as indented JSON. Exit 1 if it fails.
    """
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "--url",
        default=os.environ.get(MCP_URL_VAR, DEFAULT_MCP_URL),
        help=f"the MCP URL (default: ${MCP_URL_VAR}, else {DEFAULT_MCP_URL})",
    )
    parser.add_argument("--tool", required=True, help="the tool to call")
    parser.add_argument(
        "--arguments",
        default="{}",
        help="the tool's arguments as a JSON object",
    )
    parsed = parser.parse_args(args)
    print(f"MCP server: {parsed.url}")
    for name in list_tools(parsed.url):
        print(f"tool: {name}")
    print(f"call: {parsed.tool} {parsed.arguments}")
    try:
        result = call_tool(parsed.url, parsed.tool, json.loads(parsed.arguments))
    except RuntimeError as e:
        print(f"error: {e}")
        return 1
    print(json.dumps(result, indent=2))
    return 0
