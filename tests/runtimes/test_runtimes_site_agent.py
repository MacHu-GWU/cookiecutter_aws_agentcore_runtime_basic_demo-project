# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import (
    LOCAL_MCP_URL,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import (
    get_weather,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import (
    strip_thinking,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import (
    MCP_ARN_ENV_VAR,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import (
    AwsSigV4Auth,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import (
    get_runtime_mcp_url,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import (
    get_mcp_connection,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import make_agent
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import app
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import invoke
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent import main

import pytest

import time
import socket
import threading

import httpx
import uvicorn

from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes import site_agent
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.power_plant_mcp import mcp


@pytest.fixture(scope="module")
def mcp_url():
    """Run the real PowerPlantMcp server on a free local port for this module."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    config = uvicorn.Config(
        mcp.streamable_http_app(),
        host="127.0.0.1",
        port=port,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}/mcp"
    server.should_exit = True
    thread.join()


def test_get_weather():
    assert get_weather.tool_name == "get_weather"
    assert get_weather(41.1, -105.9)["safe_for_inspection"] is False


def test_strip_thinking():
    text = "<thinking> windy,\n so no </thinking>\n\nNo, too windy."
    assert strip_thinking(text) == "No, too windy."
    assert strip_thinking("<response> No. </response>") == "No."
    assert strip_thinking("plain") == "plain"


RUNTIME_ARN = "arn:aws:bedrock-agentcore:us-east-1:111122223333:runtime/AcRtDemo_dev_PowerPlantMcp-abc"


def test_aws_sigv4_auth(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIDEXAMPLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)
    monkeypatch.delenv("AWS_PROFILE", raising=False)
    auth = AwsSigV4Auth("us-east-1")
    request = httpx.Request("POST", get_runtime_mcp_url(RUNTIME_ARN), content=b"{}")
    signed = next(auth.auth_flow(request))
    assert signed.headers["Authorization"].startswith(
        "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/"
    )
    assert (
        "/us-east-1/bedrock-agentcore/aws4_request" in signed.headers["Authorization"]
    )
    assert "X-Amz-Date" in signed.headers


def test_get_runtime_mcp_url():
    assert get_runtime_mcp_url(RUNTIME_ARN) == (
        "https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/"
        "arn%3Aaws%3Abedrock-agentcore%3Aus-east-1%3A111122223333"
        "%3Aruntime%2FAcRtDemo_dev_PowerPlantMcp-abc/invocations?qualifier=DEFAULT"
    )


def test_get_mcp_connection(monkeypatch):
    monkeypatch.delenv("MCP_URL", raising=False)
    monkeypatch.delenv(MCP_ARN_ENV_VAR, raising=False)
    assert get_mcp_connection() == (LOCAL_MCP_URL, None)

    monkeypatch.setenv(MCP_ARN_ENV_VAR, RUNTIME_ARN)
    url, auth = get_mcp_connection()
    assert url == get_runtime_mcp_url(RUNTIME_ARN)
    assert isinstance(auth, AwsSigV4Auth)
    assert auth.region == "us-east-1"

    monkeypatch.setenv("MCP_URL", "http://example.com/mcp")
    assert get_mcp_connection() == ("http://example.com/mcp", None)


def test_make_agent(monkeypatch, mcp_url):
    """The agent loads the MCP tools over HTTP; no LLM call is made."""
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    agent = make_agent("us.amazon.nova-2-lite-v1:0", mcp_url)
    try:
        assert sorted(agent.tool_names) == [
            "get_site",
            "get_technician",
            "get_weather",
            "list_assets",
            "list_sites",
        ]
    finally:
        agent.cleanup()


class FakeAgent:
    def __init__(self):
        self.cleaned = False

    def __call__(self, prompt):
        return f"<thinking>hmm</thinking> answer to {prompt}"

    def cleanup(self):
        self.cleaned = True


def test_invoke(monkeypatch):
    monkeypatch.delenv("MCP_URL", raising=False)
    monkeypatch.delenv(MCP_ARN_ENV_VAR, raising=False)
    fake_agent = FakeAgent()
    monkeypatch.setattr(site_agent, "make_agent", lambda *args: fake_agent)
    assert invoke({"prompt": "hi"}) == {"result": "answer to hi"}
    assert fake_agent.cleaned is True


def test_main(monkeypatch):
    calls = []
    monkeypatch.setattr(app, "run", lambda: calls.append("run"))
    main()
    assert calls == ["run"]


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.site_agent",
        preview=False,
    )
