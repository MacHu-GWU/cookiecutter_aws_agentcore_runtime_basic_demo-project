# -*- coding: utf-8 -*-

"""
Generate an agentcore/agentcore.json that declares nothing, for the current
environment (ENV_NAME), so that `agentcore deploy --yes` destroys its stack.
`mise run ac-gen` brings the real project back.
"""

from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.gen import (
    main_teardown,
)


if __name__ == "__main__":
    main_teardown()
