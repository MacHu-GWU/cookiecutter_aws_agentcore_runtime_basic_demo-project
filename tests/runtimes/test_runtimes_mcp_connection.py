# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.mcp_connection import (
    get_local_mcp_url_env_var,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.mcp_connection import (
    get_runtime_arn_env_var,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.mcp_connection import (
    get_arn_region,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.mcp_connection import (
    get_runtime_mcp_url,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.mcp_connection import (
    AwsSigV4Auth,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.mcp_connection import (
    get_deployed_mcp_connection,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.mcp_connection import (
    get_mcp_connection,
)

import boto3
import httpx
import pytest

RUNTIME_ARN = (
    "arn:aws:bedrock-agentcore:us-west-2:111122223333:runtime/MyProject_dev_MyMcp-abc"
)
ARN_VAR = "AGENTCORE_RUNTIME_MYMCP_ARN"
URL_VAR = "MCP_URL_MYMCP"


def fake_session() -> boto3.Session:
    return boto3.Session(
        aws_access_key_id="AKIDEXAMPLE",
        aws_secret_access_key="secret",
        region_name="us-east-1",
    )


def test_env_var_names():
    # the name bind() sets, a contract with the AgentCore CLI
    assert get_runtime_arn_env_var("MyMcp") == ARN_VAR
    # the name the local tasks set
    assert get_local_mcp_url_env_var("MyMcp") == URL_VAR


def test_get_runtime_mcp_url():
    assert get_arn_region(RUNTIME_ARN) == "us-west-2"
    assert get_runtime_mcp_url(RUNTIME_ARN) == (
        "https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/"
        "arn%3Aaws%3Abedrock-agentcore%3Aus-west-2%3A111122223333"
        "%3Aruntime%2FMyProject_dev_MyMcp-abc/invocations?qualifier=DEFAULT"
    )


def test_aws_sigv4_auth():
    auth = AwsSigV4Auth(
        credentials=fake_session().get_credentials(), region="us-west-2"
    )
    request = httpx.Request("POST", get_runtime_mcp_url(RUNTIME_ARN), content=b"{}")
    signed = next(auth.auth_flow(request))
    authorization = signed.headers["Authorization"]
    assert authorization.startswith("AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/")
    assert "/us-west-2/bedrock-agentcore/aws4_request" in authorization
    assert "X-Amz-Date" in signed.headers


def test_get_deployed_mcp_connection():
    """The runtime's URL, signed in the ARN's region, not the session's."""
    url, auth = get_deployed_mcp_connection(RUNTIME_ARN, fake_session())
    assert url == get_runtime_mcp_url(RUNTIME_ARN)
    assert isinstance(auth, AwsSigV4Auth)
    assert auth.region == "us-west-2"


def test_get_mcp_connection(monkeypatch):
    monkeypatch.delenv(URL_VAR, raising=False)
    monkeypatch.delenv(ARN_VAR, raising=False)
    session = fake_session()
    # nothing set: an error that names both variables and bind()
    with pytest.raises(ValueError, match=f"{URL_VAR}.*bind.*{ARN_VAR}"):
        get_mcp_connection("MyMcp", session)
    # deployed: the runtime's URL, signed
    monkeypatch.setenv(ARN_VAR, RUNTIME_ARN)
    url, auth = get_mcp_connection("MyMcp", session)
    assert url == get_runtime_mcp_url(RUNTIME_ARN)
    assert isinstance(auth, AwsSigV4Auth)
    # a local URL wins
    monkeypatch.setenv(URL_VAR, "http://localhost:18731/mcp")
    assert get_mcp_connection("MyMcp", session) == ("http://localhost:18731/mcp", None)
    # another MCP runtime's variables do not count
    with pytest.raises(ValueError, match="OtherMcp"):
        get_mcp_connection("OtherMcp", session)


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.mcp_connection",
        preview=False,
    )
