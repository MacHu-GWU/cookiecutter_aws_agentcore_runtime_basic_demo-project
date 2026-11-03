# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.runtime_dir import (
    export_requirements,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.runtime_dir import (
    render_pyproject_toml,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.runtime_dir import (
    assemble_runtime_dir,
)

import sys
import json
import tomllib
import subprocess

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import PACKAGE_NAME


def test_export_requirements():
    """Only the agentcore group, pinned; none of the dev-machine dependencies."""
    requirements = export_requirements()
    names = [line.split("==")[0] for line in requirements]
    assert "mcp" in names
    assert "strands-agents" in names
    assert "aws-cdk-lib" not in names
    assert "cdk-mate" not in names
    for line in requirements:
        assert "==" in line


def test_render_pyproject_toml():
    content = render_pyproject_toml(
        "SiteAgent",
        ["mcp==1.0.0", "pywin32==312 ; sys_platform == 'win32'"],
    )
    data = tomllib.loads(content)
    assert data["project"]["name"] == "siteagent"
    assert data["project"]["requires-python"] == ">=3.12"
    assert (
        data["project"]["dependencies"][1] == "pywin32==312 ; sys_platform == 'win32'"
    )


def test_assemble_runtime_dir(tmp_path):
    """The copied code imports on its own: nothing outside the copied subpackages."""
    dir_runtime = tmp_path / "SiteAgent"
    path_stale = dir_runtime / PACKAGE_NAME / "stale.py"
    path_stale.parent.mkdir(parents=True)
    path_stale.write_text("")
    path_venv = dir_runtime / ".venv" / "keep"
    path_venv.parent.mkdir()
    path_venv.write_text("")
    assemble_runtime_dir(
        dir_runtime=dir_runtime,
        name="SiteAgent",
        module="runtimes.site_agent",
        protocol="HTTP",
        requirements=["mcp==1.0.0"],
    )
    assert not path_stale.exists()
    assert path_venv.exists()
    main_py = (dir_runtime / "main.py").read_text()
    assert "runtimes.site_agent import main\n" in main_py
    assert "runtimes.site_agent import app\n" in main_py
    assert 'if __name__ == "__main__":' in main_py
    code = (
        f"import sys, json; sys.path.insert(0, {str(dir_runtime)!r}); "
        f"import {PACKAGE_NAME}.runtimes.site_agent as m; "
        f"import {PACKAGE_NAME}.runtimes.power_plant_mcp; "
        "print(m.__file__); "
        f"print(json.dumps([k for k in sys.modules if k.startswith('{PACKAGE_NAME}.')]))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.splitlines()
    assert lines[0].startswith(str(dir_runtime))
    for name in json.loads(lines[1]):
        assert name.split(".")[1] in ["power_plant", "runtimes"]


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.runtime_dir",
        preview=False,
    )
