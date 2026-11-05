# -*- coding: utf-8 -*-

"""
How an agent runtime reaches an MCP runtime: locally, at a URL, without auth;
deployed, at the invocation URL of the MCP runtime's ARN, every request signed
with SigV4.

The ARN comes from ``bind()`` in ``agentcore/cdk/lib/cdk-stack.ts``:
``runtime('<Mcp>').bind(runtime('<Agent>'))`` grants the agent's execution role
``bedrock-agentcore:InvokeAgentRuntime`` on the MCP runtime and sets the agent's
environment variable :func:`get_runtime_arn_env_var` of the MCP runtime's name.
"""

from __future__ import annotations

import typing as T
import os
import urllib.parse

import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from .common import LOCAL_MCP_URL

if T.TYPE_CHECKING:  # pragma: no cover
    import boto3
    from botocore.credentials import Credentials

MCP_URL_VAR = "MCP_URL"
"""
The URL of the MCP server, when set: the local mise tasks point an agent at a
local server with it. It wins over the deployed ARN.
"""

SIGV4_SERVICE = "bedrock-agentcore"
"""
The service name a request to AgentCore Runtime is signed for.
"""


def get_runtime_arn_env_var(runtime_name: str) -> str:
    """
    The environment variable ``bind()`` sets to the ARN of the runtime
    ``runtime_name`` (its name in ``agentcore.json``), such as
    ``AGENTCORE_RUNTIME_MYMCP_ARN`` for ``MyMcp``. Undocumented AgentCore CLI
    behavior: check it again after upgrading ``@aws/agentcore``.
    """
    return f"AGENTCORE_RUNTIME_{runtime_name.upper()}_ARN"


def get_arn_region(runtime_arn: str) -> str:
    """
    The region of a runtime ARN, its fourth field.
    """
    return runtime_arn.split(":")[3]


def get_runtime_mcp_url(runtime_arn: str) -> str:
    """
    The MCP URL of a deployed MCP runtime, from its ARN.
    """
    region = get_arn_region(runtime_arn)
    quoted_arn = urllib.parse.quote(runtime_arn, safe="")
    return (
        f"https://bedrock-agentcore.{region}.amazonaws.com"
        f"/runtimes/{quoted_arn}/invocations?qualifier=DEFAULT"
    )


class AwsSigV4Auth(httpx.Auth):
    """
    Sign each HTTP request with SigV4 for :data:`SIGV4_SERVICE`. A runtime with
    no authorizer configured accepts only such requests (``AWS_IAM``).

    :param credentials: refreshable credentials, such as the runtime's execution
        role; frozen again for each request.
    :param region: the region of the runtime called.
    """

    requires_request_body = True  # the body is signed

    def __init__(self, credentials: Credentials, region: str):
        self.credentials = credentials
        self.region = region

    def auth_flow(self, request: httpx.Request):
        aws_request = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers={"host": request.url.host},
        )
        signer = SigV4Auth(
            self.credentials.get_frozen_credentials(),
            SIGV4_SERVICE,
            self.region,
        )
        signer.add_auth(aws_request)
        request.headers.update(dict(aws_request.headers))
        yield request


def get_mcp_connection(
    arn_env_var: str,
    boto_session: boto3.Session,
    url_env_var: str = MCP_URL_VAR,
    default_url: str = LOCAL_MCP_URL,
) -> tuple[str, httpx.Auth | None]:
    """
    Where to reach an MCP server, as ``(url, auth)``, in this order:

    1. ``url_env_var`` is set (local runs): that URL, no auth.
    2. ``arn_env_var`` is set (deployed, by ``bind()``): the runtime's MCP URL,
       signed with the credentials of ``boto_session``.
    3. Otherwise ``default_url``, no auth.

    :param arn_env_var: from :func:`get_runtime_arn_env_var`.
    :param boto_session: whose credentials sign the requests; only read in case 2.
    """
    if url_env_var in os.environ:
        return os.environ[url_env_var], None
    if arn_env_var in os.environ:
        runtime_arn = os.environ[arn_env_var]
        auth = AwsSigV4Auth(
            credentials=boto_session.get_credentials(),
            region=get_arn_region(runtime_arn),
        )
        return get_runtime_mcp_url(runtime_arn), auth
    return default_url, None
