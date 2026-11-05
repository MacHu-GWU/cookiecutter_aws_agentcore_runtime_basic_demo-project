# -*- coding: utf-8 -*-

"""
Run a runtime of the registry on a developer machine, or call it there:
``local_run --runtime <Name> --mode local|dev|call``. The generated tasks
``ac-local-<slug>``, ``ac-dev-<slug>``, and ``ac-local-<slug>-call`` call it, so
no per-runtime command is written by hand.

- ``local``: the package from the repo (runtime ``local``, config from the files).
- ``dev``: the packaged copy under ``agentcore dev`` (runtime ``agentcore_local``,
  config from SSM); run ``ac-gen`` first.
- ``call``: the runtime's sample payload, sent to its local port, by
  :mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.devtools.mcp_client` or
  :mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agent_client`.

A server listens on the runtime's ``local_port``; an agent's MCP runtimes are
reached at theirs, through one ``MCP_URL_<NAME>`` variable each. ``local`` and
``dev`` first stop a leftover server of this project on the port.
"""

from __future__ import annotations

import os
import sys
import json
import argparse

from ..env import env
from ..paths import PACKAGE_NAME
from ..config.api import Config
from ..runtimes.common import MCP_PATH
from ..runtimes.common import MCP_PORT_VAR
from ..runtimes.mcp_connection import get_local_mcp_url_env_var
from ..agentcore_project.registry import RuntimeSpec
from ..agentcore_project.registry import RuntimeProtocolEnum
from ..agentcore_project.registry import get_runtime_specs
from .local_port import PortHeldByOtherError
from .local_port import free_port
from . import mcp_client
from . import agent_client

MODES = ["local", "dev", "call"]


def get_local_url(spec: RuntimeSpec) -> str:
    """
    The URL of the runtime on its local port: the MCP endpoint of an MCP
    runtime, the base URL of an agent.
    """
    if spec.protocol == RuntimeProtocolEnum.MCP:
        return f"http://localhost:{spec.local_port}{MCP_PATH}"
    return f"http://localhost:{spec.local_port}"


def get_mcp_url_env(spec: RuntimeSpec, specs: list[RuntimeSpec]) -> dict[str, str]:
    """
    For an agent: one ``MCP_URL_<NAME>`` per MCP runtime it calls, pointing at
    that runtime's local port.
    """
    by_name = {other.name: other for other in specs}
    return {
        get_local_mcp_url_env_var(name): get_local_url(by_name[name])
        for name in spec.mcp_runtimes
    }


def get_local_command(
    spec: RuntimeSpec,
    specs: list[RuntimeSpec],
) -> tuple[dict[str, str], list[str]]:
    """
    The extra environment and the command line that serve the package from the
    repo: an MCP runtime's ``main()``, or an agent's ``app`` with uvicorn.
    """
    module = f"{PACKAGE_NAME}.{spec.module}"
    if spec.protocol == RuntimeProtocolEnum.MCP:
        return {MCP_PORT_VAR: str(spec.local_port)}, [sys.executable, "-m", module]
    argv = [
        sys.executable,
        "-m",
        "uvicorn",
        f"{module}:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(spec.local_port),
    ]
    return get_mcp_url_env(spec, specs), argv


def get_dev_command(
    spec: RuntimeSpec,
    specs: list[RuntimeSpec],
    config: Config,
) -> tuple[dict[str, str], list[str]]:
    """
    The extra environment and the command line that serve the packaged copy
    with ``agentcore dev``, always with ``--port`` (without it, the CLI silently
    moves to the next free port). ``AWS_REGION`` is the config's: on
    ``agentcore_local`` the session takes the region from it, because the
    config is read through that session.
    """
    extra_env = {"AWS_REGION": config.aws_region, **get_mcp_url_env(spec, specs)}
    argv = [
        "agentcore",
        "dev",
        "--agent",
        spec.name,
        "--no-traces",
        "--port",
        str(spec.local_port),
    ]
    return extra_env, argv


def get_call_args(spec: RuntimeSpec) -> list[str]:
    """
    The arguments of the client ``main()`` that sends the runtime's sample
    payload to its local port.
    """
    url = get_local_url(spec)
    payload = spec.sample_payload
    if spec.protocol == RuntimeProtocolEnum.MCP:
        params = payload["params"]
        return [
            "--url",
            url,
            "--tool",
            params["name"],
            "--arguments",
            json.dumps(params.get("arguments", {})),
        ]
    return ["--url", url, "--prompt", payload["prompt"]]


def serve(extra_env: dict[str, str], argv: list[str], port: int) -> int:
    """
    Free ``port``, then replace this process with ``argv``, run with the current
    environment plus ``extra_env``. Returns only if the port is held by a
    process outside this project: 1.
    """
    try:
        pids = free_port(port)
    except PortHeldByOtherError as e:
        print(f"local_run: {e}")
        return 1
    if pids:
        print(f"local_run: stopped {pids}, a leftover server on port {port}")
    for name, value in extra_env.items():
        print(f"{name}={value}")
    print(" ".join(argv), flush=True)
    os.execvpe(argv[0], argv, {**os.environ, **extra_env})
    return 0  # pragma: no cover (execvpe does not return)


def run(runtime_name: str, mode: str, config: Config) -> int:
    """
    Run or call the runtime ``runtime_name`` of the registry, in ``mode``.

    :raises ValueError: no such runtime.
    """
    specs = get_runtime_specs(config)
    by_name = {spec.name: spec for spec in specs}
    if runtime_name not in by_name:
        raise ValueError(f"no runtime {runtime_name!r}; one of {sorted(by_name)}")
    spec = by_name[runtime_name]
    if mode == "local":
        return serve(*get_local_command(spec, specs), port=spec.local_port)
    if mode == "dev":
        return serve(*get_dev_command(spec, specs, config), port=spec.local_port)
    client = mcp_client if spec.protocol == RuntimeProtocolEnum.MCP else agent_client
    return client.main(get_call_args(spec))


def main(args: list[str] | None = None) -> int:
    """
    ``local_run --runtime <Name> --mode local|dev|call``, with the local config
    of ``ENV_NAME``.
    """
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--runtime", required=True, help="its name in agentcore.json")
    parser.add_argument("--mode", required=True, choices=MODES)
    parsed = parser.parse_args(args)
    config = Config.load_from_local_config_file(env_name=env.current_env_name)
    return run(parsed.runtime, parsed.mode, config)
