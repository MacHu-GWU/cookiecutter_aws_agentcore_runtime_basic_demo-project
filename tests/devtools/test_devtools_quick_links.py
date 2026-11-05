# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.quick_links import (
    QuickLink,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.quick_links import (
    get_env_links,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.quick_links import (
    render_quick_links,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.quick_links import (
    get_env_boto_session,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.quick_links import (
    read_deployed_runtimes,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.quick_links import (
    generate_quick_links,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.quick_links import main

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import path_enum
from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config
from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.mise_tasks import (
    get_stack_targets,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools import quick_links
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client import (
    DeployedRuntime,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.registry import (
    get_runtime_specs,
)

ROLE_ARN = "arn:aws:iam::111122223333:role/AgentCore-MyProject-dev-SiteAgentRole-abc"


def deployed_site_agent() -> dict[str, DeployedRuntime]:
    return {
        "MyProject_dev_SiteAgent": DeployedRuntime(
            physical_name="MyProject_dev_SiteAgent",
            runtime_id="MyProject_dev_SiteAgent-xyz",
            runtime_arn="arn:aws:bedrock-agentcore:us-east-1:111122223333:runtime/MyProject_dev_SiteAgent-xyz",
            role_arn=ROLE_ARN,
        )
    }


def test_quick_link_row():
    assert (
        QuickLink("Stack", "s", "https://x").to_row() == "| Stack | [`s`](https://x) |"
    )
    assert QuickLink("Runtime", "r", note="not deployed").to_row() == (
        "| Runtime | `r`: not deployed |"
    )


def test_get_env_links(config: Config):
    """
    The stacks and the config parameter from the config; per runtime, three
    links when deployed, one row when not; no account ID anywhere.
    """
    specs = get_runtime_specs(config)
    links = get_env_links(
        config, get_stack_targets("dev"), specs, deployed_site_agent()
    )
    resources = [link.resource for link in links]
    assert resources[:5] == [
        "CloudFormation stack, alerts",
        "CloudFormation stack, publisher",
        "CloudFormation stack, agentcore_deps",
        "CloudFormation stack, AgentCore runtimes",
        "SSM parameter, config",
    ]
    assert resources[5:] == [
        "AgentCore runtime, PowerPlantMcp",
        "AgentCore runtime, SiteAgent",
        "IAM role, SiteAgent execution",
        "CloudWatch log group, SiteAgent",
    ]
    by_resource = {link.resource: link for link in links}
    assert by_resource["AgentCore runtime, PowerPlantMcp"].note == "not deployed"
    agent = by_resource["AgentCore runtime, SiteAgent"]
    assert agent.url.endswith("/bedrock-agentcore/agents/MyProject_dev_SiteAgent-xyz")
    role = by_resource["IAM role, SiteAgent execution"]
    assert role.name == "AgentCore-MyProject-dev-SiteAgentRole-abc"
    text = render_quick_links({"dev": links})
    assert "111122223333" not in text


def test_get_env_links_not_read(config: Config):
    specs = get_runtime_specs(config)
    links = get_env_links(config, {}, specs, PermissionError("/secret/path"))
    notes = [link.note for link in links if link.url is None]
    assert notes == ["not read (PermissionError)"] * 2
    assert "/secret/path" not in render_quick_links({"dev": links})


def test_render_quick_links():
    text = render_quick_links(
        {
            "dev": [QuickLink("Stack", "s", "https://x")],
            "prd": FileNotFoundError("/Users/me/config-prd-secret.json5"),
        }
    )
    assert text.startswith("# Quick Links\n")
    assert "## dev\n\n| Resource | Console |\n| :--- | :--- |\n| Stack |" in text
    assert "ERROR: cannot load the config of `prd`: `FileNotFoundError`." in text
    assert "/Users/me" not in text


def test_get_env_boto_session(config: Config, monkeypatch):
    monkeypatch.delenv("AWS_PROFILE_FOR_DEV", raising=False)
    session = get_env_boto_session(config)
    assert session.region_name == "us-east-1"


def test_read_deployed_runtimes(config: Config, monkeypatch):
    """A failure to read is returned, not raised."""
    specs = get_runtime_specs(config)
    monkeypatch.setenv("AWS_PROFILE_FOR_DEV", "no-such-profile-for-this-test")
    assert isinstance(read_deployed_runtimes(config, specs), Exception)
    monkeypatch.delenv("AWS_PROFILE_FOR_DEV")
    monkeypatch.setattr(
        quick_links, "find_deployed_runtimes", lambda client, names: {"x": names}
    )
    found = read_deployed_runtimes(config, specs)
    assert found == {"x": ["MyProject_dev_PowerPlantMcp", "MyProject_dev_SiteAgent"]}


def test_generate_quick_links(tmp_path, capsys, monkeypatch):
    """Every environment; written only when it changed; never reads AWS here."""
    path = tmp_path / "QUICK_LINKS.md"

    def read(config, specs):
        if config.env_name == "tst":
            return PermissionError("denied")
        return {}

    assert generate_quick_links(path, read=read) is True
    out = capsys.readouterr().out
    assert "dev: 0 of 2 runtimes deployed" in out
    assert "tst: runtimes not read: PermissionError" in out
    text = path.read_text()
    for env_name in ["dev", "tst", "prd"]:
        assert f"## {env_name}" in text
    assert generate_quick_links(path, read=read) is False
    assert "already up to date" in capsys.readouterr().out
    # a config that does not load
    monkeypatch.setattr(
        quick_links.Config,
        "load_from_local_config_file",
        classmethod(lambda cls, env_name: (_ for _ in ()).throw(FileNotFoundError())),
    )
    assert generate_quick_links(path, read=read) is True
    assert "ERROR: cannot load the config" in capsys.readouterr().out


def test_main(tmp_path, monkeypatch):
    monkeypatch.setattr(path_enum, "path_quick_links_md", tmp_path / "QUICK_LINKS.md")
    monkeypatch.setattr(quick_links, "read_deployed_runtimes", lambda config, specs: {})
    main()
    assert (tmp_path / "QUICK_LINKS.md").exists()


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.devtools.quick_links",
        preview=False,
    )
