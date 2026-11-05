# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.site_agent import (
    SYSTEM_PROMPT,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.site_agent import TOOLS
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.site_agent import (
    SiteAgentRequest,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.site_agent import (
    SiteAgentResponse,
)

import typing as T

import pytest
from pydantic import BaseModel
from pydantic import ValidationError


def test_system_prompt():
    assert "inspections" in SYSTEM_PROMPT


def test_tools():
    """
    Every tool is a plain function a framework can describe to the LLM: a
    docstring, type hints on every parameter, and a Pydantic result.
    """
    assert TOOLS
    for func in TOOLS:
        assert func.__doc__.strip()
        hints = T.get_type_hints(func)
        result = hints.pop("return")
        assert issubclass(result, BaseModel)
        assert set(hints) == set(func.__code__.co_varnames[: func.__code__.co_argcount])


def test_request_and_response():
    """The payload contract: a non-empty prompt in, a result out; every field described."""
    assert SiteAgentRequest.model_validate({"prompt": "hi"}).prompt == "hi"
    for payload in [{}, {"prompt": ""}, {"question": "hi"}]:
        with pytest.raises(ValidationError):
            SiteAgentRequest.model_validate(payload)
    assert SiteAgentResponse(result="ok").model_dump() == {"result": "ok"}
    for model in [SiteAgentRequest, SiteAgentResponse]:
        for field in model.model_json_schema()["properties"].values():
            assert field["description"]


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.site_agent",
        preview=False,
    )
