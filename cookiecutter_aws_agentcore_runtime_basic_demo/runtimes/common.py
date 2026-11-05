# -*- coding: utf-8 -*-

"""
What every runtime module in this subpackage shares: the settings AgentCore
Runtime requires of an MCP server, the decorator that gives a tool its
business function's docstring, and the startup print.
"""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from ..one.api import one

MCP_PORT_VAR = "FASTMCP_PORT"
"""
The port an MCP server listens on. Unset on AgentCore Runtime, so the server
uses :data:`MCP_DEFAULT_PORT`; ``agentcore dev`` and the ``ac-local-*`` mise
tasks set it to their local port.
"""

MCP_DEFAULT_PORT = 8000
"""
The port AgentCore Runtime sends MCP requests to.
"""

MCP_PATH = "/mcp"
"""
The path AgentCore Runtime sends MCP requests to; the FastMCP default.
"""

MCP_TRANSPORT = "streamable-http"
"""
The MCP transport AgentCore Runtime speaks.
"""


def get_mcp_port() -> int:
    """
    The port of :data:`MCP_PORT_VAR`, else :data:`MCP_DEFAULT_PORT`.
    """
    return int(os.environ.get(MCP_PORT_VAR, str(MCP_DEFAULT_PORT)))


def new_mcp_server(name: str) -> FastMCP:
    """
    A FastMCP server with the settings of the AgentCore MCP protocol contract:
    every interface (``0.0.0.0``), the port of :func:`get_mcp_port`, the path
    :data:`MCP_PATH`, and ``stateless_http=True`` (no server-side MCP session;
    AgentCore still routes a client's requests to the same microVM by its
    ``Mcp-Session-Id``). The same settings work locally.

    :param name: the server name, the runtime's name in ``agentcore.json``.
    """
    return FastMCP(
        name,
        host="0.0.0.0",
        port=get_mcp_port(),
        streamable_http_path=MCP_PATH,
        stateless_http=True,
    )


def run_mcp_server(mcp: FastMCP) -> None:
    """
    Serve ``mcp`` over :data:`MCP_TRANSPORT`, blocking until stopped.
    """
    mcp.run(transport=MCP_TRANSPORT)


def doc_from(func):
    """
    A decorator that gives the decorated tool the docstring of the business
    function ``func``, which becomes the tool description the LLM reads.

    ``functools.wraps`` would not do: it also copies the signature, so the
    injected dependency (such as the engine) would show in the tool's schema.
    """

    def decorator(tool_func):
        tool_func.__doc__ = func.__doc__
        return tool_func

    return decorator


def print_config_source() -> None:
    """
    Load the config, and print which environment and runtime it is for. Each
    runtime's ``main()`` calls it before serving, so a runtime that cannot read
    its config fails at startup, with the reason in its log.
    """
    print(
        f"Loaded the config of {one.config.env_name!r} "
        f"on runtime {one.runtime.current_runtime_name()!r}",
        flush=True,
    )
