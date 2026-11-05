# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agent_client import (
    invoke_agent,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agent_client import main

import httpx
import pytest


def test_invoke_agent(agent_url):
    assert invoke_agent(agent_url, {"prompt": "hi"}) == {
        "result": "answer to hi in session None"
    }
    # the session ID reaches the agent through the AgentCore header
    answer = invoke_agent(agent_url, {"prompt": "hi"}, session_id="s" * 33)
    assert answer == {"result": f"answer to hi in session {'s' * 33}"}
    with pytest.raises(httpx.HTTPStatusError):
        invoke_agent(agent_url, {"prompt": "fail"})


def test_main(agent_url, monkeypatch, capsys):
    assert main(["--url", agent_url, "--prompt", "hi", "--session-id", "abc"]) == 0
    out = capsys.readouterr().out
    assert "answer to hi in session abc" in out
    monkeypatch.setenv("AGENT_URL", agent_url)
    assert main(["--prompt", "fail"]) == 1
    assert "error: " in capsys.readouterr().out


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agent_client",
        preview=False,
    )
