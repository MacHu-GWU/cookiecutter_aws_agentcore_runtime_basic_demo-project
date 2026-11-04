# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.gen import main
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.gen import (
    main_teardown,
)

import json

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import path_enum
from cookiecutter_aws_agentcore_runtime_basic_demo.env import env


def test_main(monkeypatch, tmp_path):
    """Generate every file into a temp dir, for the current environment only."""
    monkeypatch.setattr(path_enum, "path_agentcore_json", tmp_path / "agentcore.json")
    monkeypatch.setattr(
        path_enum, "path_aws_targets_json", tmp_path / "aws-targets.json"
    )
    monkeypatch.setattr(path_enum, "dir_agentcore_app", tmp_path / "app")
    # env caches the environment name, so set the cached value
    monkeypatch.setitem(env.__dict__, "current_env_name", "tst")
    main()
    targets = json.loads((tmp_path / "aws-targets.json").read_text())
    assert [target["name"] for target in targets] == ["tst"]
    data = json.loads((tmp_path / "agentcore.json").read_text())
    assert {"name": "ENV_NAME", "value": "tst"} in data["runtimes"][0]["envVars"]
    assert (tmp_path / "app" / "PowerPlantMcp" / "main.py").exists()
    pyproject_toml = (tmp_path / "app" / "SiteAgent" / "pyproject.toml").read_text()
    assert 'name = "siteagent"' in pyproject_toml


def test_main_teardown(monkeypatch, tmp_path):
    """An empty agentcore.json and the target of the current environment; app/ untouched."""
    monkeypatch.setattr(path_enum, "path_agentcore_json", tmp_path / "agentcore.json")
    monkeypatch.setattr(
        path_enum, "path_aws_targets_json", tmp_path / "aws-targets.json"
    )
    monkeypatch.setattr(path_enum, "dir_agentcore_app", tmp_path / "app")
    monkeypatch.setitem(env.__dict__, "current_env_name", "prd")
    main_teardown()
    data = json.loads((tmp_path / "agentcore.json").read_text())
    assert "runtimes" not in data
    targets = json.loads((tmp_path / "aws-targets.json").read_text())
    assert [target["name"] for target in targets] == ["prd"]
    assert not (tmp_path / "app").exists()


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.gen",
        preview=False,
    )
