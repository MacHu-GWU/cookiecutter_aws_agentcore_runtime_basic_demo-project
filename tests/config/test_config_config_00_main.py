# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.config.config_00_main import Config

import pytest

from pydantic import ValidationError


class TestConfig:
    def test_validation(self):
        with pytest.raises(ValidationError):
            Config(project_name="my_project")

    def test_load_from_local_config_file(self, tmp_path):
        """
        Later files override earlier ones, and a missing secret file is skipped.
        """
        (tmp_path / "config-shared.json5").write_text(
            '{project_name: "a", log_level: "shared", agentcore_project_name: "A"}'
        )
        (tmp_path / "config-dev.json5").write_text(
            "// comment\n{aws_account_id: '1', aws_region: 'r', log_level: 'dev'}"
        )
        (tmp_path / "config-dev-secret.json5").write_text("{project_name: 'b'}")
        conf = Config.load_from_local_config_file(env_name="dev", dir_config=tmp_path)
        assert conf.project_name == "b"
        assert conf.env_name == "dev"
        assert conf.log_level == "dev"

    @pytest.mark.parametrize(
        "env_name",
        [
            "dev",
            "tst",
            "prd",
        ],
    )
    def test_load(self, env_name: str):
        """
        The committed config files, plus a secret file, load for every environment.
        """
        conf = Config.load(env_name=env_name, runtime_name="local")
        assert conf.env_name == env_name
        # from the fake secret file in conftest.py, not the real one
        assert conf.aws_account_id == "111122223333"

    def test_load_error(self):
        with pytest.raises(NotImplementedError):
            Config.load(env_name="dev", runtime_name="ci")


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.config.config_00_main",
        preview=False,
    )
