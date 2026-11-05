# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.mise_tasks import (
    get_invoke_script,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.mise_tasks import (
    render_project_env_tasks,
)

import tomllib

import pytest

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import path_enum
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.registry import (
    RuntimeSpec,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.registry import (
    RuntimeProtocolEnum,
)


def load_tasks() -> dict:
    return tomllib.loads(path_enum.path_mise_toml.read_text(encoding="utf-8"))["tasks"]


def test_mise_toml_is_up_to_date():
    """
    ``mise.toml`` holds the generated tasks of every stack, runtime, and
    environment. If this fails, run ``mise run gen-env-tasks``.
    """
    text = path_enum.path_mise_toml.read_text(encoding="utf-8")
    assert render_project_env_tasks() in text


def test_chains():
    """
    The deploy chain runs config, the agentcore-deps stack, then the runtimes;
    the teardown chain the reverse, after a confirmation; every step prints a
    banner first.
    """
    import tomllib

    tasks = tomllib.loads(path_enum.path_mise_toml.read_text(encoding="utf-8"))["tasks"]
    up = tasks["ac-chain-up-dev"]
    assert [item["task"] for item in up["run"] if isinstance(item, dict)] == [
        "config-deploy-dev",
        "cdk-up-dev-agentcore-deps-stack",
        "ac-deploy-dev",
    ]
    down = tasks["ac-chain-down-dev"]
    assert [item["task"] for item in down["run"] if isinstance(item, dict)] == [
        "ac-down-dev",
        "cdk-down-dev-agentcore-deps-stack",
        "config-delete-dev",
    ]
    # the teardown chain asks yes/no once before its first step, then tells its
    # steps not to ask again; never mise's `confirm`, which takes Enter as yes
    assert "confirm" not in down
    assert "raw" not in down
    assert down["env"] == {"CONFIRMED_BY_CHAIN": "true"}
    first_task = next(i for i, item in enumerate(down["run"]) if isinstance(item, dict))
    question = down["run"][first_task - 1]
    assert question.startswith(".venv/bin/python .mise/tasks/confirm.py --action ")
    assert "CONFIRMED_BY_CHAIN" not in question
    assert not any("confirm.py" in str(item) for item in up["run"])
    # destructive steps ask on their own, unless a chain asked already
    for name in ["ac-down-dev", "config-delete-dev"]:
        assert "raw" not in tasks[name]
        assert (
            "--skip_var CONFIRM_YES --skip_var CONFIRMED_BY_CHAIN" in tasks[name]["run"]
        )
    for name in [
        "config-deploy-dev",
        "ac-deploy-dev",
        "cdk-down-dev-agentcore-deps-stack",
    ]:
        assert "confirm.py" not in tasks[name]["run"]
    for name in [
        "config-deploy-dev",
        "ac-deploy-dev",
        "ac-down-dev",
        "cdk-up-dev-agentcore-deps-stack",
    ]:
        assert tasks[name]["run"].strip().startswith(f"echo '>>> {name}: ")
    # ac-deploy does not deploy the config itself; the chain does
    assert tasks["ac-deploy-dev"]["depends"] == ["inst"]


def test_deploy_and_test_tasks():
    """
    ac-deploy reminds to commit the deployed state; ac-test checks the status,
    then invokes every runtime once, each with its sample payload.
    """
    tasks = load_tasks()
    assert "deployed-state.json" in tasks["ac-deploy-dev"]["run"]
    assert "deployed-state.json" in tasks["ac-down-dev"]["run"]
    assert "agentcore status --target dev" in tasks["ac-status-dev"]["run"]
    test = tasks["ac-test-dev"]
    assert [item["task"] for item in test["run"] if isinstance(item, dict)] == [
        "ac-status-dev",
        "ac-invoke-dev-power-plant-mcp",
        "ac-invoke-dev-site-agent",
    ]
    mcp = tasks["ac-invoke-dev-power-plant-mcp"]["run"]
    assert "--runtime PowerPlantMcp --mcp-method tools/call --mcp-name get_site" in mcp
    agent = tasks["ac-invoke-dev-site-agent"]["run"]
    assert '--payload "$PAYLOAD" ${SESSION_ID:+--session-id $SESSION_ID}' in agent
    assert "AWS_PROFILE={{env.AWS_PROFILE_FOR_DEV}}" in agent
    assert (
        "AWS_PROFILE={{env.AWS_PROFILE_FOR_PRD}}"
        in tasks["ac-invoke-prd-site-agent"]["run"]
    )


def test_ac_down_restores_the_project():
    """
    ac-down deploys an empty project, and puts the real one back when the task
    ends, failed or not: the trap is set after the empty project is written and
    before the deploy, which is the last command that can fail.
    """
    lines = load_tasks()["ac-down-dev"]["run"].strip().splitlines()
    teardown = lines.index(".venv/bin/python .mise/tasks/ac-gen-teardown.py")
    trap = lines.index("trap '.venv/bin/python .mise/tasks/ac-gen.py' EXIT")
    deploy = next(i for i, line in enumerate(lines) if line.startswith("AWS_PROFILE="))
    assert teardown < trap < deploy
    assert lines[deploy].endswith("agentcore deploy --target dev --yes")


def test_get_invoke_script():
    spec = RuntimeSpec(
        name="MyMcp",
        module="runtimes.my_mcp",
        protocol=RuntimeProtocolEnum.MCP,
        sample_payload={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    )
    lines = get_invoke_script(spec, "dev", "dev")
    assert lines[0] == 'PAYLOAD=\'{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}\''
    assert "--mcp-method tools/list --payload" in lines[-1]
    assert "--mcp-name" not in lines[-1]
    spec.sample_payload = {"prompt": "it's"}
    with pytest.raises(ValueError, match="single quote"):
        get_invoke_script(spec, "dev", "dev")


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.mise_tasks",
        preview=False,
    )
