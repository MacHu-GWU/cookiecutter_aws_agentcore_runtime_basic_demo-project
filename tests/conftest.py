# -*- coding: utf-8 -*-

import pytest

import time
import shutil
import socket
import threading

import uvicorn

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import path_enum
from cookiecutter_aws_agentcore_runtime_basic_demo.env import EnvNameEnum
from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config


@pytest.fixture(autouse=True)
def local_runtime(monkeypatch):
    """
    Run every test as the local runtime, which loads the config from the local
    files, even on a CI runner (which sets ``CI``), and in the ``dev`` environment,
    whatever ``ENV_NAME`` the shell or ``.env`` sets.
    """
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("IS_AGENTCORE_RUNTIME", raising=False)
    monkeypatch.delenv("LOCAL_DEV", raising=False)
    monkeypatch.setenv("ENV_NAME", "dev")


@pytest.fixture(scope="session", autouse=True)
def fake_dir_config(tmp_path_factory):
    """
    Point ``path_enum.dir_config`` at a copy of the committed config files plus
    fake ``-secret`` files, so tests never read the real, git-ignored secrets and
    behave the same on a CI runner that has none.
    """
    dir_config = tmp_path_factory.mktemp("config")
    for path in path_enum.dir_config.glob("config-*.json5"):
        if not path.name.endswith("-secret.json5"):
            shutil.copy(path, dir_config / path.name)
    for env_name in EnvNameEnum:
        path = dir_config / f"config-{env_name.value}-secret.json5"
        path.write_text(
            '{aws_account_id: "111122223333", '
            'db_connection_string: "sqlite+pysqlite:///:memory:"}'
        )
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(path_enum, "dir_config", dir_config)
        yield dir_config


@pytest.fixture
def config() -> Config:
    """
    A config with fixed sample values, independent of the files in ``config/``.
    """
    return Config(
        project_name="my_project",
        env_name="dev",
        aws_account_id="111122223333",
        aws_region="us-east-1",
        log_level="DEBUG",
        agentcore_project_name="MyProject",
        db_connection_string="sqlite+pysqlite:///:memory:",
        site_agent_model_id="us.amazon.nova-2-lite-v1:0",
    )


@pytest.fixture(scope="session")
def mcp_url():
    """
    Serve the real ``PowerPlantMcp`` server on a free local port for the whole
    test session, and give its MCP URL: what an agent or a client connects to.
    """
    from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.power_plant_mcp import (
        mcp,
    )

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    config = uvicorn.Config(
        mcp.streamable_http_app(),
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/mcp"
    server.should_exit = True
    thread.join()
