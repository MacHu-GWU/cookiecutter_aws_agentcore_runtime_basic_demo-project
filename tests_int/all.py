# -*- coding: utf-8 -*-

"""
Integration tests: they read the stacks deployed in the current environment
(``ENV_NAME``) with ``AWS_PROFILE_FOR_<ENV>``, so they run only after a deploy.
Run them with ``mise run int-test``.
"""

if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_unit_test

    run_unit_test(__file__)
