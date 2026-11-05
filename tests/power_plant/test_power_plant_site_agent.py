# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.site_agent import (
    SYSTEM_PROMPT,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.site_agent import TOOLS

import typing as T

from pydantic import BaseModel


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


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.site_agent",
        preview=False,
    )
