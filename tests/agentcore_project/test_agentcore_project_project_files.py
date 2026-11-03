# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.project_files import (
    get_runtime_specs,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.project_files import (
    build_agentcore_json,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.project_files import (
    build_aws_targets_json,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.project_files import (
    load_all_configs,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.project_files import (
    write_json,
)

import json

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import path_enum
from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config


def test_get_runtime_specs(config: Config):
    names = [spec.name for spec in get_runtime_specs(config)]
    assert names == ["PowerPlantMcp", "SiteAgent"]


def test_build_agentcore_json(config: Config):
    data = build_agentcore_json(config)
    assert data["name"] == "MyProject"
    assert data["runtimes"][0]["codeLocation"] == "app/PowerPlantMcp"
    assert data["runtimes"][1]["protocol"] == "HTTP"


def test_agentcore_json_is_up_to_date():
    """The committed agentcore.json matches the config; else run ``mise run ac-gen``."""
    config = Config.load_from_local_config_file(env_name="dev")
    data = json.loads(path_enum.path_agentcore_json.read_text(encoding="utf-8"))
    assert data == build_agentcore_json(config)


def test_cdk_stack_ts_uses_the_runtime_names():
    """cdk-stack.ts binds the runtimes by the names the config gives them."""
    config = Config.load_from_local_config_file(env_name="dev")
    content = path_enum.path_agentcore_cdk_stack_ts.read_text(encoding="utf-8")
    for spec in get_runtime_specs(config):
        assert f"runtime('{spec.name}')" in content


def test_build_aws_targets_json(config: Config):
    targets = build_aws_targets_json([config])
    assert targets == [
        {
            "name": "dev",
            "description": "The dev environment",
            "account": "111122223333",
            "region": "us-east-1",
        }
    ]


def test_load_all_configs():
    names = [config.env_name for config in load_all_configs()]
    assert names == ["dev", "tst", "prd"]


def test_write_json(tmp_path):
    path = tmp_path / "data.json"
    assert write_json(path, {"a": 1}) is True
    assert write_json(path, {"a": 1}) is False
    assert json.loads(path.read_text()) == {"a": 1}


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.project_files",
        preview=False,
    )
