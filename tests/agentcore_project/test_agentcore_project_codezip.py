# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.codezip import (
    check_codezip_install,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.codezip import (
    export_requirements,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.codezip import (
    render_pyproject_toml,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.codezip import (
    assemble_runtime_dir,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.codezip import (
    check_codezip_installs,
)

import sys
import json
import tomllib
import subprocess

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import PACKAGE_NAME
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project import codezip
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.registry import (
    RuntimeProtocolEnum,
)

#: Run in a subprocess before importing the copied code: the dev-machine-only
#: packages cannot be imported, as in a runtime, which does not install them.
BLOCK_DEV_PACKAGES = """
import sys, importlib.abc
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in ("aws_cdk", "cdk_mate", "json5"):
            raise ImportError(f"{name} is not installed in a runtime")
sys.meta_path.insert(0, Block())
"""


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
    """
    The copied code imports on its own: nothing outside the copied modules, and
    no dev-machine-only package.
    """
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
        protocol=RuntimeProtocolEnum.HTTP,
        requirements=["mcp==1.0.0"],
    )
    assert not path_stale.exists()
    assert path_venv.exists()
    main_py = (dir_runtime / "main.py").read_text()
    assert "runtimes.site_agent import main\n" in main_py
    assert "runtimes.site_agent import app\n" in main_py
    assert 'if __name__ == "__main__":' in main_py
    # dev-machine tooling is never copied
    for name in ["cdk", "agentcore_project", "devtools"]:
        assert not (dir_runtime / PACKAGE_NAME / name).exists()
    code = BLOCK_DEV_PACKAGES + (
        f"import sys, json; sys.path.insert(0, {str(dir_runtime)!r}); "
        f"import {PACKAGE_NAME}.runtimes.site_agent as m; "
        f"import {PACKAGE_NAME}.runtimes.power_plant_mcp; "
        f"from {PACKAGE_NAME}.one.api import one; "
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
    allowed = ["config", "one", "power_plant", "runtimes"]
    allowed += ["constants", "env", "paths", "runtime"]
    for name in json.loads(lines[1]):
        assert name.split(".")[1] in allowed


def test_check_codezip_install(tmp_path):
    """
    The locked dependencies install as ``agentcore deploy`` installs them; a
    requirement that cannot be met fails, with uv's message naming the package.
    """
    path = tmp_path / "pyproject.toml"
    path.write_text(render_pyproject_toml("SiteAgent", export_requirements()))
    assert check_codezip_install(path) is None
    path.write_text(render_pyproject_toml("SiteAgent", ["sqlalchemy==0.0.1"]))
    error = check_codezip_install(path)
    assert "aarch64-manylinux_2_34" in error
    assert "sqlalchemy" in error


def test_assemble_mcp_runtime_dir(tmp_path):
    """An MCP runtime's shim exposes main only: agentcore dev runs it as a script."""
    assemble_runtime_dir(
        dir_runtime=tmp_path,
        name="MyMcp",
        module="runtimes.power_plant_mcp",
        protocol=RuntimeProtocolEnum.MCP,
        requirements=[],
    )
    main_py = (tmp_path / "main.py").read_text()
    assert "import main\n" in main_py
    assert "import app" not in main_py


def test_check_codezip_installs(tmp_path, monkeypatch, capsys):
    for name in ["GoodMcp", "BadAgent"]:
        (tmp_path / name).mkdir()
        (tmp_path / name / "pyproject.toml").write_text("")

    def fake_check(path):
        return None if path.parent.name == "GoodMcp" else "no wheel for sqlalchemy"

    monkeypatch.setattr(codezip, "check_codezip_install", fake_check)
    assert check_codezip_installs(tmp_path) is False
    out = capsys.readouterr().out
    assert "OK: the dependencies of GoodMcp" in out
    assert "ERROR: the dependencies of BadAgent" in out
    assert "no wheel for sqlalchemy" in out
    (tmp_path / "BadAgent" / "pyproject.toml").unlink()
    assert check_codezip_installs(tmp_path) is True


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.codezip",
        preview=False,
    )
