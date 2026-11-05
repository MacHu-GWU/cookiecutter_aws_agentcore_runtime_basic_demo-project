# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client import (
    new_session_id,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client import (
    find_runtime_arn,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client import (
    get_runtime_id,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client import (
    get_runtime_log_group,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client import (
    invoke_agent_runtime,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client import (
    get_deployed_mcp_connection,
)

import io
import json

import boto3
import pytest
from botocore.stub import Stubber
from botocore.response import StreamingBody

from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.mcp_connection import (
    AwsSigV4Auth,
)

ARN = (
    "arn:aws:bedrock-agentcore:us-east-1:111122223333:runtime/MyProject_dev_MyAgent-abc"
)


def fake_session() -> boto3.Session:
    return boto3.Session(
        aws_access_key_id="AKIDEXAMPLE",
        aws_secret_access_key="secret",
        region_name="us-east-1",
    )


def test_new_session_id():
    first = new_session_id("user-1")
    assert first.startswith("user-1-")
    assert len(first) >= 33
    assert new_session_id("user-1") != first


def test_find_runtime_arn():
    client = fake_session().client("bedrock-agentcore-control")
    runtime = dict(
        agentRuntimeId="MyProject_dev_MyAgent-abc",
        agentRuntimeVersion="1",
        description="a runtime",
        lastUpdatedAt="2026-01-01T00:00:00Z",
        status="READY",
    )
    with Stubber(client) as stubber:
        stubber.add_response(
            "list_agent_runtimes",
            {
                "agentRuntimes": [
                    {
                        **runtime,
                        "agentRuntimeName": "MyProject_dev_MyMcp",
                        "agentRuntimeArn": ARN + "x",
                    },
                ],
                "nextToken": "page-2",
            },
        )
        stubber.add_response(
            "list_agent_runtimes",
            {
                "agentRuntimes": [
                    {
                        **runtime,
                        "agentRuntimeName": "MyProject_dev_MyAgent",
                        "agentRuntimeArn": ARN,
                    }
                ]
            },
            {"nextToken": "page-2"},
        )
        assert find_runtime_arn(client, "MyProject_dev_MyAgent") == ARN
        stubber.add_response("list_agent_runtimes", {"agentRuntimes": []})
        with pytest.raises(ValueError, match="no deployed runtime"):
            find_runtime_arn(client, "MyProject_dev_Missing")


def test_log_group():
    assert get_runtime_id(ARN) == "MyProject_dev_MyAgent-abc"
    assert get_runtime_log_group(ARN) == (
        "/aws/bedrock-agentcore/runtimes/MyProject_dev_MyAgent-abc-DEFAULT"
    )


def test_invoke_agent_runtime():
    client = fake_session().client("bedrock-agentcore")
    body = json.dumps({"result": "hi"}).encode("utf-8")
    session_id = "s" * 33
    with Stubber(client) as stubber:
        stubber.add_response(
            "invoke_agent_runtime",
            {
                "runtimeSessionId": session_id,
                "contentType": "application/json",
                "statusCode": 200,
                "response": StreamingBody(io.BytesIO(body), len(body)),
            },
            {
                "agentRuntimeArn": ARN,
                "qualifier": "DEFAULT",
                "payload": b'{"prompt": "hello"}',
                "contentType": "application/json",
                "accept": "application/json",
                "runtimeSessionId": session_id,
            },
        )
        answer, returned_id = invoke_agent_runtime(
            client, ARN, {"prompt": "hello"}, session_id=session_id
        )
    assert answer == {"result": "hi"}
    assert returned_id == session_id


def test_get_deployed_mcp_connection():
    url, auth = get_deployed_mcp_connection(ARN, fake_session())
    assert url.startswith("https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/")
    assert isinstance(auth, AwsSigV4Auth)
    assert auth.region == "us-east-1"


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client",
        preview=False,
    )
