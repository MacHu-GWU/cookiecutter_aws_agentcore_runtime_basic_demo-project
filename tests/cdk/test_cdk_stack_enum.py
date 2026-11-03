# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_enum import StackEnum

import aws_cdk as cdk

from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config
from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import One
from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_ctx_enum import (
    StackCtxEnum,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_ctx_enum import (
    list_entry_names,
)


def test_entries_match_stack_ctx_enum():
    """
    Layer 2 has exactly the entries of layer 1, in the same order.
    """
    assert list_entry_names(StackEnum) == list_entry_names(StackCtxEnum)


def test_synth(config: Config, tmp_path):
    """
    Every stack is synthesized under its stack name, and the dependency wired by
    attribute access becomes a stack dependency.
    """
    one = One()
    one.config = config
    se = StackEnum(app=cdk.App(outdir=str(tmp_path)), one=one)
    se.synth()
    names = sorted(p.name for p in tmp_path.glob("*.template.json"))
    assert names == [
        "my-project-dev-agentcore-deps.template.json",
        "my-project-dev-alerts.template.json",
        "my-project-dev-publisher.template.json",
    ]
    assert se.alerts in se.publisher.dependencies
    assert se.get("alerts") is se.alerts
    assert se.get_all() == [se.alerts, se.publisher, se.agentcore_deps]


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_enum",
        preview=False,
    )
