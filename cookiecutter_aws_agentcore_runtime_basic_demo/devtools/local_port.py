# -*- coding: utf-8 -*-

"""
Free a local TCP port held by a leftover dev server of this project, such as
one in a terminal you forgot to stop.

A process counts as this project's when its working directory is inside the
project root: every local server task runs there (``agentcore dev`` runs its
servers in ``app/<Runtime>/``). If any process on the port is not this
project's, nothing is stopped and :class:`PortHeldByOtherError` is raised.

Stopping sends ``SIGTERM`` (a clean shutdown) and waits; only processes still
listening after the wait get ``SIGKILL``. Needs ``lsof`` and ``ps`` (macOS, Linux).
"""

from __future__ import annotations

import os
import time
import signal
import argparse
import subprocess
from pathlib import Path

from ..paths import path_enum


class PortHeldByOtherError(RuntimeError):
    """
    The port is held by a process that is not this project's.
    """


def find_listening_pids(port: int) -> list[int]:
    """
    The IDs of the processes listening on TCP ``port``, sorted.

    ``lsof`` only sees the current user's processes, unless run as root.
    """
    result = subprocess.run(
        ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
        capture_output=True,
        text=True,
    )
    # lsof exits with 1, and prints nothing, when no process matches.
    return sorted({int(line) for line in result.stdout.split()})


def get_process_cwd(pid: int) -> Path | None:
    """
    The working directory of process ``pid``, or None if it cannot be read.
    """
    result = subprocess.run(
        ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        if line.startswith("n"):
            return Path(line[1:])
    return None


def get_process_command(pid: int) -> str:
    """
    The command line of process ``pid``, or an empty string if it has exited.
    """
    result = subprocess.run(
        ["ps", "-o", "command=", "-p", str(pid)],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def is_own_process(pid: int, dir_root: Path) -> bool:
    """
    Whether process ``pid`` runs with its working directory inside ``dir_root``.
    """
    cwd = get_process_cwd(pid)
    if cwd is None:
        return False
    return cwd.resolve().is_relative_to(dir_root.resolve())


def _send_signal(pids: list[int], sig: signal.Signals) -> None:
    for pid in pids:
        try:
            os.kill(pid, sig)
        except ProcessLookupError:  # it has exited already
            pass


def _wait_until_free(port: int, timeout: float) -> list[int]:
    deadline = time.monotonic() + timeout
    while True:
        pids = find_listening_pids(port)
        if not pids or time.monotonic() >= deadline:
            return pids
        time.sleep(0.1)


def free_port(
    port: int,
    dir_root: Path = path_enum.dir_project_root,
    timeout: float = 5.0,
) -> list[int]:
    """
    Stop the processes of this project listening on TCP ``port``.

    :param port: the port, 1024 to 65535.
    :param dir_root: a process counts as this project's when its working
        directory is inside this directory.
    :param timeout: seconds to wait after ``SIGTERM``, and again after ``SIGKILL``.
    :returns: the IDs of the processes stopped; empty if the port was free.
    :raises PortHeldByOtherError: a process on the port is not this project's;
        no process is stopped.
    """
    if not 1024 <= port <= 65535:
        raise ValueError(f"port must be between 1024 and 65535, got {port}")
    pids = find_listening_pids(port)
    others = [pid for pid in pids if not is_own_process(pid, dir_root)]
    if others:
        lines = [f"  pid {pid}: {get_process_command(pid)}" for pid in others]
        raise PortHeldByOtherError(
            f"port {port} is held by a process outside {dir_root}; "
            "stop it yourself or choose another port:\n" + "\n".join(lines)
        )
    if not pids:
        return []
    _send_signal(pids, signal.SIGTERM)
    remaining = _wait_until_free(port, timeout)
    if remaining:
        _send_signal(remaining, signal.SIGKILL)
        remaining = _wait_until_free(port, timeout)
    if remaining:  # pragma: no cover
        raise RuntimeError(f"port {port} is still held by {remaining}")
    return pids


def main(args: list[str] | None = None) -> int:
    """
    ``free-port.py --port <port>``: free the port, then exit 0; exit 1 if it is
    held by a process that is not this project's.
    """
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--port", type=int, required=True, help="TCP port to free")
    port = parser.parse_args(args).port
    try:
        pids = free_port(port)
    except PortHeldByOtherError as e:
        print(f"free-port: {e}")
        return 1
    if pids:
        print(
            f"free-port: stopped {pids}, a leftover server of this project on port {port}"
        )
    return 0
