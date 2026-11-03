# -*- coding: utf-8 -*-

"""
Delete the config of the current environment (ENV_NAME) from SSM Parameter Store.
"""

from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import one

if __name__ == "__main__":
    one.delete_config()
