# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_port import (
    PortHeldByOtherError,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_port import (
    find_listening_pids,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_port import (
    get_process_cwd,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_port import (
    get_process_command,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_port import (
    is_own_process,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_port import (
    free_port,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_port import (
    main,
)

import sys
import time
import socket
import subprocess

import pytest

from cookiecutter_aws_agentcore_runtime_basic_demo.devtools import local_port

#: A server that ignores SIGTERM, so only SIGKILL stops it.
STUBBORN_SERVER = """
import signal, socket, sys, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
sock = socket.socket()
sock.bind(("127.0.0.1", int(sys.argv[1])))
sock.listen()
time.sleep(60)
"""


def get_free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start_server(cwd, port: int, code: str | None = None) -> subprocess.Popen:
    """Start a listening Python process in ``cwd``, and wait until it listens."""
    if code is None:
        args = [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"]
    else:
        args = [sys.executable, "-c", code, str(port)]
    process = subprocess.Popen(
        args,
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 10
    while process.pid not in find_listening_pids(port):
        assert time.monotonic() < deadline, "the test server did not start"
        time.sleep(0.05)
    return process


@pytest.fixture
def server(tmp_path):
    port = get_free_port()
    process = start_server(tmp_path, port)
    yield port, process
    process.kill()
    process.wait()


def test_find_listening_pids(server):
    port, process = server
    assert find_listening_pids(port) == [process.pid]
    assert find_listening_pids(get_free_port()) == []


def test_get_process_info(server, tmp_path):
    _, process = server
    assert get_process_cwd(process.pid).resolve() == tmp_path.resolve()
    assert "http.server" in get_process_command(process.pid)
    assert is_own_process(process.pid, tmp_path) is True
    assert is_own_process(process.pid, tmp_path / "other") is False


def test_get_process_info_of_exited_process():
    process = subprocess.Popen([sys.executable, "-c", "pass"])
    process.wait()
    assert get_process_cwd(process.pid) is None
    assert get_process_command(process.pid) == ""
    assert is_own_process(process.pid, local_port.path_enum.dir_project_root) is False
    # signal 0 only checks that the process exists, so a reused pid is not hurt
    local_port._send_signal([process.pid], 0)  # no error


def test_free_port_when_free(tmp_path):
    assert free_port(get_free_port(), dir_root=tmp_path) == []


def test_free_port_stops_own_server(server, tmp_path):
    port, process = server
    assert free_port(port, dir_root=tmp_path) == [process.pid]
    assert process.wait(timeout=5) is not None
    assert find_listening_pids(port) == []


def test_free_port_refuses_other_server(server, tmp_path):
    port, process = server
    with pytest.raises(PortHeldByOtherError, match="http.server"):
        free_port(port, dir_root=tmp_path / "other")
    assert process.poll() is None  # still running


def test_free_port_kills_server_ignoring_sigterm(tmp_path):
    port = get_free_port()
    process = start_server(tmp_path, port, code=STUBBORN_SERVER)
    try:
        assert free_port(port, dir_root=tmp_path, timeout=0.5) == [process.pid]
        assert process.wait(timeout=5) == -9
    finally:
        process.kill()
        process.wait()


def test_free_port_rejects_bad_port(tmp_path):
    with pytest.raises(ValueError):
        free_port(80, dir_root=tmp_path)


def test_main(monkeypatch, capsys):
    monkeypatch.setattr(local_port, "free_port", lambda port: [])
    assert main(["--port", "18731"]) == 0
    assert capsys.readouterr().out == ""

    monkeypatch.setattr(local_port, "free_port", lambda port: [123])
    assert main(["--port", "18731"]) == 0
    assert "stopped [123]" in capsys.readouterr().out

    def raise_other(port):
        raise PortHeldByOtherError("held by someone else")

    monkeypatch.setattr(local_port, "free_port", raise_other)
    assert main(["--port", "18731"]) == 1
    assert "held by someone else" in capsys.readouterr().out


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_port",
        preview=False,
    )
