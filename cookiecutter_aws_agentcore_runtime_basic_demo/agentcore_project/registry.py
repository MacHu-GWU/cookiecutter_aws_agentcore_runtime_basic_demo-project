# -*- coding: utf-8 -*-

"""
The runtime registry: every AgentCore Runtime of the project, in one list.

This is the one place a runtime is declared. ``agentcore/agentcore.json`` and
each runtime's code directory ``app/<Runtime>/`` are generated from it.
"""

from __future__ import annotations

import re
import enum
import dataclasses

from ..config.api import Config

#: The Python of every runtime; the dev Python, ``[tools] python`` in ``mise.toml``.
RUNTIME_PYTHON = "3.12"

#: :data:`RUNTIME_PYTHON` as AgentCore names it in ``agentcore.json``.
RUNTIME_VERSION = "PYTHON_" + RUNTIME_PYTHON.replace(".", "_")


class RuntimeProtocolEnum(enum.StrEnum):
    """
    The protocol AgentCore Runtime speaks with a runtime.
    """

    #: An MCP server: streamable HTTP on port 8000, path ``/mcp``.
    MCP = "MCP"
    #: An agent: ``POST /invocations`` and ``GET /ping`` on port 8080.
    HTTP = "HTTP"


@dataclasses.dataclass
class RuntimeSpec:
    """
    One AgentCore Runtime of the project.
    """

    # fmt: off
    name: str = dataclasses.field()  #: Name in ``agentcore.json``, from ``agentcore_runtime_name_*`` of the config.
    module: str = dataclasses.field()  #: The runtime module, relative to the package, such as ``runtimes.my_mcp``: it has a ``main()``, and an ``app`` for ``HTTP``.
    protocol: RuntimeProtocolEnum = dataclasses.field()  #: How AgentCore talks to it.
    sample_payload: dict = dataclasses.field()  #: What ``ac-invoke-<env>-<slug>`` sends to the deployed runtime: ``{"prompt": ...}`` for an agent, a whole JSON-RPC request for an MCP server.
    # fmt: on

    @property
    def slug(self) -> str:
        """
        The runtime's name in task names, such as ``my-mcp`` for ``MyMcp``.
        """
        return re.sub(r"(?<!^)(?=[A-Z])", "-", self.name).lower()


def get_runtime_specs(config: Config) -> list[RuntimeSpec]:
    """
    Every runtime of the project. To add one: its names in the config, its
    runtime module, and a line here.
    """
    return [
        RuntimeSpec(
            name=config.agentcore_runtime_name_power_plant_mcp,
            module="runtimes.power_plant_mcp",
            protocol=RuntimeProtocolEnum.MCP,
            sample_payload={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "get_site", "arguments": {"site_id": "S-03"}},
            },
        ),
        RuntimeSpec(
            name=config.agentcore_runtime_name_site_agent,
            module="runtimes.site_agent",
            protocol=RuntimeProtocolEnum.HTTP,
            sample_payload={
                "prompt": (
                    "Can we send someone to inspect the turbines at site S-03 "
                    "tomorrow? Who is assigned there?"
                ),
            },
        ),
    ]
