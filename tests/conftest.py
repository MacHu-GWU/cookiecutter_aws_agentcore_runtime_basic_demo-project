# -*- coding: utf-8 -*-

import pytest

import shutil

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import path_enum
from cookiecutter_aws_agentcore_runtime_basic_demo.env import EnvNameEnum
from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config


@pytest.fixture(autouse=True)
def local_runtime(monkeypatch):
    """
    Run every test as the local runtime, the only one that can load the config,
    even on a CI runner (which sets ``CI``), and in the ``dev`` environment,
    whatever ``ENV_NAME`` the shell or ``.env`` sets.
    """
    monkeypatch.delenv("CI", raising=False)
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
        path.write_text('{aws_account_id: "111122223333"}')
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
    )
