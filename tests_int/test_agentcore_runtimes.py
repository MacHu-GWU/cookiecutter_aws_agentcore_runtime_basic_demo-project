# -*- coding: utf-8 -*-

"""
The deployed AgentCore runtimes of the current environment answer, called the
way a client program calls them: the MCP runtime over SigV4, the agent runtime
through ``InvokeAgentRuntime``, twice in one runtime session. It calls the
agent's model.
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
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agentcore_client import (
    get_deployed_mcp_connection,
)

from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import one
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.mcp_client import (
    list_tools,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.mcp_client import (
    call_tool,
)


def test_mcp_runtime():
    """The MCP runtime lists its tools and answers a call, over SigV4."""
    config = one.config
    runtime_arn = find_runtime_arn(
        one.bedrock_agentcore_control_client,
        config.agentcore_runtime_physical_name_power_plant_mcp,
    )
    url, auth = get_deployed_mcp_connection(runtime_arn, one.boto_ses)
    assert "get_site" in list_tools(url, auth=auth)
    site = call_tool(url, "get_site", {"site_id": "S-03"}, auth=auth)
    assert site["id"] == "S-03"


def test_agent_runtime():
    """
    The agent answers, and a second message of the same session continues the
    conversation in the same runtime session.
    """
    config = one.config
    runtime_arn = find_runtime_arn(
        one.bedrock_agentcore_control_client,
        config.agentcore_runtime_physical_name_site_agent,
    )
    session_id = new_session_id("int-test")
    client = one.bedrock_agentcore_client
    answer, returned_id = invoke_agent_runtime(
        client,
        runtime_arn,
        {"prompt": "Who is assigned to site S-03? Answer with the names only."},
        session_id=session_id,
    )
    print(answer)
    assert returned_id == session_id
    assert answer["result"]
    answer, returned_id = invoke_agent_runtime(
        client,
        runtime_arn,
        {"prompt": "Which of them is also assigned to site S-04?"},
        session_id=session_id,
    )
    print(answer)
    assert returned_id == session_id
    assert answer["result"]


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_unit_test

    run_unit_test(__file__)
