# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.gen import main

import json

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import path_enum


def test_main(monkeypatch, tmp_path):
    """Generate every file into a temp dir, for the current environment only."""
    monkeypatch.setattr(path_enum, "path_agentcore_json", tmp_path / "agentcore.json")
    monkeypatch.setattr(
        path_enum, "path_aws_targets_json", tmp_path / "aws-targets.json"
    )
    monkeypatch.setattr(path_enum, "dir_agentcore_app", tmp_path / "app")
    monkeypatch.setenv("ENV_NAME", "tst")
    main()
    targets = json.loads((tmp_path / "aws-targets.json").read_text())
    assert [target["name"] for target in targets] == ["tst"]
    data = json.loads((tmp_path / "agentcore.json").read_text())
    assert {"name": "ENV_NAME", "value": "tst"} in data["runtimes"][0]["envVars"]
    assert (tmp_path / "app" / "PowerPlantMcp" / "main.py").exists()
    pyproject_toml = (tmp_path / "app" / "SiteAgent" / "pyproject.toml").read_text()
    assert 'name = "siteagent"' in pyproject_toml


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.gen",
        preview=False,
    )
