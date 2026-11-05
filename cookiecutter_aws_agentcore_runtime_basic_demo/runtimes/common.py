# -*- coding: utf-8 -*-

"""
What every runtime module in this subpackage shares: the settings AgentCore
Runtime requires of an MCP server, the decorator that gives a tool its
business function's docstring, the one agent of an agent runtime's process,
the cleanup of a model's answer, and the startup print.
"""

from __future__ import annotations

import typing as T
import os
import re
import threading
import contextlib

from mcp.server.fastmcp import FastMCP

from ..one.api import one

if T.TYPE_CHECKING:  # pragma: no cover
    from strands import Agent

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


#: Some models (such as Nova) wrap their reasoning in ``<thinking>`` tags.
_THINKING_PATTERN = re.compile(r"<thinking>.*?</thinking>", re.DOTALL)

#: Some models (such as Nova) wrap the answer itself in ``<response>`` tags.
_RESPONSE_TAG_PATTERN = re.compile(r"</?response>")


def strip_thinking(text: str) -> str:
    """
    Remove ``<thinking>...</thinking>`` blocks and ``<response>`` tags from a
    model's answer: they are not part of the answer.
    """
    text = _THINKING_PATTERN.sub("", text)
    text = _RESPONSE_TAG_PATTERN.sub("", text)
    return text.strip()


class ProcessAgent:
    """
    The one agent of an agent runtime's process, built on first use by
    ``build`` and kept for the life of the process.

    AgentCore gives each runtime session its own microVM and process, so this
    agent serves exactly one session: its MCP connections stay open, so its MCP
    sessions do too (the MCP microVMs stay warm), and it remembers the earlier
    turns of the conversation. Callers continue a conversation by sending the
    same runtime session ID.

    Calls run one at a time: an agent cannot run two at once, and the requests
    of one session are one conversation. A call that raises (such as on a broken
    MCP connection) drops the agent, so the next call builds a new one; the
    conversation so far is lost.

    :param build: makes the agent, with the dependencies of this process. It
        runs on the first call, never at import time: a microVM is restored from
        a snapshot, and credentials made at import time would be stale.
    """

    def __init__(self, build: T.Callable[[], Agent]):
        self._build = build
        self._agent: Agent | None = None
        self._lock = threading.Lock()

    def get(self) -> Agent:
        """
        The agent, built if there is none yet.
        """
        if self._agent is None:
            self._agent = self._build()
        return self._agent

    def reset(self) -> None:
        """
        Close and drop the agent, so the next call builds a new one. A failing
        cleanup is ignored: the agent is dropped anyway.
        """
        agent, self._agent = self._agent, None
        if agent is not None:
            with contextlib.suppress(Exception):
                agent.cleanup()

    def __call__(self, prompt: str) -> str:
        """
        Ask the agent ``prompt``; returns its answer as text.
        """
        with self._lock:
            agent = self.get()
            try:
                return str(agent(prompt))
            except Exception:
                self.reset()
                raise
