# -*- coding: utf-8 -*-

"""
Every deployed AgentCore runtime of the current environment answers, called the
way a client program calls it: each MCP runtime over SigV4, each agent runtime
through ``InvokeAgentRuntime``, twice in one runtime session. The runtimes and
what to send them come from the runtime registry (``sample_payload``), so a new
runtime is tested here without a new test. It calls the agents' models.
"""

from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client import (
    new_session_id,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client import (
    find_runtime_arn,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client import (
    invoke_agent_runtime,
)

import pytest

from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import one
from cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.mcp_connection import (
    get_deployed_mcp_connection,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.mcp_client import (
    list_tools,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.mcp_client import (
    call_tool,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.registry import (
    RuntimeSpec,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.registry import (
    RuntimeProtocolEnum,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.registry import (
    get_runtime_specs,
)

SPECS = get_runtime_specs(one.config)
MCP_SPECS = [spec for spec in SPECS if spec.protocol == RuntimeProtocolEnum.MCP]
AGENT_SPECS = [spec for spec in SPECS if spec.protocol == RuntimeProtocolEnum.HTTP]

#: The second message of an agent's session: it only makes sense with the first.
FOLLOW_UP_PROMPT = "Repeat the main point of your previous answer in one sentence."


def find_arn(spec: RuntimeSpec) -> str:
    """
    The ARN of the deployed runtime of ``spec`` in the current environment.
    """
    return find_runtime_arn(
        one.bedrock_agentcore_control_client,
        one.config.get_agentcore_runtime_physical_name(spec.name),
    )


@pytest.mark.parametrize("spec", MCP_SPECS, ids=lambda spec: spec.name)
def test_mcp_runtime(spec: RuntimeSpec):
    """
    The MCP runtime lists its tools and answers its sample call, over SigV4;
    a tool error fails the test.
    """
    url, auth = get_deployed_mcp_connection(find_arn(spec), one.boto_ses)
    tool_names = list_tools(url, auth=auth)
    print(tool_names)
    assert tool_names
    payload = spec.sample_payload
    if payload["method"] == "tools/call":
        params = payload["params"]
        assert params["name"] in tool_names
        result = call_tool(url, params["name"], params.get("arguments"), auth=auth)
        print(result)


@pytest.mark.parametrize("spec", AGENT_SPECS, ids=lambda spec: spec.name)
def test_agent_runtime(spec: RuntimeSpec):
    """
    The agent answers its sample prompt, and a follow-up in the same session
    runs in that same runtime session.
    """
    runtime_arn = find_arn(spec)
    session_id = new_session_id("int-test")
    client = one.bedrock_agentcore_client
    for payload in [spec.sample_payload, {"prompt": FOLLOW_UP_PROMPT}]:
        answer, returned_id = invoke_agent_runtime(
            client,
            runtime_arn,
            payload,
            session_id=session_id,
        )
        print(answer)
        assert returned_id == session_id
        assert answer["result"]


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_unit_test

    run_unit_test(__file__)
