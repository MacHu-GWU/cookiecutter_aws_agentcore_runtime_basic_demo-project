# -*- coding: utf-8 -*-

"""
A client of the deployed runtimes, for scripts and integration tests: find a
runtime's ARN by its name, invoke an agent runtime with a runtime session ID,
reach an MCP runtime over SigV4, and name a runtime's log group.

Every function takes its AWS clients or session as arguments, such as those of
``one``; none builds its own.
"""

from __future__ import annotations

import typing as T
import json
import uuid

from ..runtimes.mcp_connection import AwsSigV4Auth
from ..runtimes.mcp_connection import get_arn_region
from ..runtimes.mcp_connection import get_runtime_mcp_url

if T.TYPE_CHECKING:  # pragma: no cover
    import boto3
    from mypy_boto3_bedrock_agentcore.client import BedrockAgentCoreClient
    from mypy_boto3_bedrock_agentcore_control.client import (
        BedrockAgentCoreControlClient,
    )

#: The endpoint every runtime gets.
DEFAULT_QUALIFIER = "DEFAULT"

#: AgentCore rejects a runtime session ID shorter than this.
MIN_SESSION_ID_LENGTH = 33


def new_session_id(prefix: str = "session") -> str:
    """
    A new runtime session ID, such as ``<prefix>-<uuid4>``: make one per
    conversation (and per user), keep it on the client, and send it with every
    message of that conversation.
    """
    session_id = f"{prefix}-{uuid.uuid4()}"
    if len(session_id) < MIN_SESSION_ID_LENGTH:  # pragma: no cover
        raise ValueError(f"session ID {session_id!r} is too short")
    return session_id


def find_runtime_arn(
    control_client: BedrockAgentCoreControlClient,
    physical_name: str,
) -> str:
    """
    The ARN of the deployed runtime whose name is ``physical_name``, such as
    ``agentcore_runtime_physical_name_<x>`` of the config. The ARN ends in an ID
    assigned at deploy time, so it is looked up, never built.

    :raises ValueError: no such runtime is deployed.
    """
    paginator = control_client.get_paginator("list_agent_runtimes")
    for page in paginator.paginate():
        for runtime in page["agentRuntimes"]:
            if runtime["agentRuntimeName"] == physical_name:
                return runtime["agentRuntimeArn"]
    raise ValueError(f"no deployed runtime named {physical_name!r}")


def get_runtime_id(runtime_arn: str) -> str:
    """
    The runtime ID, the last part of its ARN, such as ``MyProject_dev_MyMcp-abc``.
    """
    return runtime_arn.split("/")[-1]


def get_runtime_log_group(runtime_arn: str, qualifier: str = DEFAULT_QUALIFIER) -> str:
    """
    The CloudWatch log group of a runtime endpoint; each runtime session writes
    its own log stream in it.
    """
    return f"/aws/bedrock-agentcore/runtimes/{get_runtime_id(runtime_arn)}-{qualifier}"


def invoke_agent_runtime(
    client: BedrockAgentCoreClient,
    runtime_arn: str,
    payload: dict,
    session_id: str | None = None,
    qualifier: str = DEFAULT_QUALIFIER,
) -> tuple[dict, str]:
    """
    Send ``payload`` to the deployed agent runtime ``runtime_arn``, through
    ``InvokeAgentRuntime``, and read the whole answer.

    :param session_id: the runtime session to continue; ``None`` starts a new
        one (a cold start). Reuse the returned ID for the next message of the
        same conversation.

    :returns: the JSON answer, and the runtime session ID it ran in.
    """
    kwargs = dict(
        agentRuntimeArn=runtime_arn,
        qualifier=qualifier,
        payload=json.dumps(payload).encode("utf-8"),
        contentType="application/json",
        accept="application/json",
    )
    if session_id is not None:
        kwargs["runtimeSessionId"] = session_id
    response = client.invoke_agent_runtime(**kwargs)
    answer = json.loads(response["response"].read())
    return answer, response["runtimeSessionId"]


def get_deployed_mcp_connection(
    runtime_arn: str,
    boto_session: boto3.Session,
) -> tuple[str, AwsSigV4Auth]:
    """
    The MCP URL of the deployed MCP runtime ``runtime_arn`` and the SigV4 auth
    to call it with the credentials of ``boto_session``: pass both to
    :mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.devtools.mcp_client`.
    """
    auth = AwsSigV4Auth(
        credentials=boto_session.get_credentials(),
        region=get_arn_region(runtime_arn),
    )
    return get_runtime_mcp_url(runtime_arn), auth
