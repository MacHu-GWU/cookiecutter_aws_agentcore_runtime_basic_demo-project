# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_ctx_enum import (
    list_entry_names,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_ctx_enum import (
    StackCtxEnum,
)

from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config
from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import One


def test_list_entry_names():
    assert list_entry_names(StackCtxEnum) == ["alerts", "publisher", "agentcore_deps"]


class TestStackCtxEnum:
    def test_entries(self, config: Config):
        """
        Names, account, and region come from one.config, the session is one.bsm;
        nothing calls AWS.
        """
        one = One()
        one.config = config
        stack_ctx_enum = StackCtxEnum(one=one)
        stack_ctx = stack_ctx_enum.alerts
        assert stack_ctx.construct_id == "my-project-dev-alerts"
        assert stack_ctx.stack_name == "my-project-dev-alerts"
        assert stack_ctx.aws_account_id == "111122223333"
        assert stack_ctx.aws_region == "us-east-1"
        assert stack_ctx.bsm is one.bsm
        assert stack_ctx_enum.publisher.stack_name == "my-project-dev-publisher"
        assert stack_ctx_enum.get("alerts") is stack_ctx
        assert stack_ctx_enum.get_all() == [
            stack_ctx,
            stack_ctx_enum.publisher,
            stack_ctx_enum.agentcore_deps,
        ]


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_ctx_enum",
        preview=False,
    )
