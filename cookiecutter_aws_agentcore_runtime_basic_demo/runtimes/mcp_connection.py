# -*- coding: utf-8 -*-

"""
How an agent runtime reaches an MCP runtime: locally, at the URL of its own
environment variable, without auth; deployed, at the invocation URL of the MCP
runtime's ARN, every request signed with SigV4. A client of a deployed MCP
runtime (``devtools/``, ``tests_int/``) uses the same
:func:`get_deployed_mcp_connection`.

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

if T.TYPE_CHECKING:  # pragma: no cover
    import boto3
    from botocore.credentials import Credentials

SIGV4_SERVICE = "bedrock-agentcore"
"""
The service name a request to AgentCore Runtime is signed for.
"""


def get_local_mcp_url_env_var(runtime_name: str) -> str:
    """
    The environment variable that points an agent at a local server of the MCP
    runtime ``runtime_name``, such as ``MCP_URL_MYMCP`` for ``MyMcp``: the local
    tasks set it, and it wins over the deployed ARN.
    """
    return f"MCP_URL_{runtime_name.upper()}"


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


def get_deployed_mcp_connection(
    runtime_arn: str,
    boto_session: boto3.Session,
) -> tuple[str, AwsSigV4Auth]:
    """
    The MCP URL of the deployed MCP runtime ``runtime_arn``, and the SigV4 auth
    that signs each request with the credentials of ``boto_session``, in the
    region of the ARN.
    """
    auth = AwsSigV4Auth(
        credentials=boto_session.get_credentials(),
        region=get_arn_region(runtime_arn),
    )
    return get_runtime_mcp_url(runtime_arn), auth


def get_mcp_connection(
    runtime_name: str,
    boto_session: boto3.Session,
) -> tuple[str, httpx.Auth | None]:
    """
    Where an agent reaches the MCP runtime ``runtime_name`` (its name in
    ``agentcore.json``), as ``(url, auth)``, in this order:

    1. :func:`get_local_mcp_url_env_var` is set (local runs): that URL, no auth.
    2. :func:`get_runtime_arn_env_var` is set (deployed, by ``bind()``):
       :func:`get_deployed_mcp_connection`.

    :param boto_session: whose credentials sign the requests; only read in case 2.

    :raises ValueError: neither is set. Deployed, the ``bind()`` line of this
        pair is missing in ``cdk-stack.ts``; locally, the agent was started
        without the ``ac-local-<slug>`` / ``ac-dev-<slug>`` task. Failing here
        names the cause; a default URL would fail later, as a connection error.
    """
    url_env_var = get_local_mcp_url_env_var(runtime_name)
    arn_env_var = get_runtime_arn_env_var(runtime_name)
    if url_env_var in os.environ:
        return os.environ[url_env_var], None
    if arn_env_var in os.environ:
        return get_deployed_mcp_connection(os.environ[arn_env_var], boto_session)
    raise ValueError(
        f"no MCP connection for {runtime_name!r}: set {url_env_var} (local), or "
        f"bind {runtime_name!r} to this agent in agentcore/cdk/lib/cdk-stack.ts, "
        f"which sets {arn_env_var} (deployed)"
    )
