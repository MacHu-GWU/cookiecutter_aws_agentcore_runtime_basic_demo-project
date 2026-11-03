# -*- coding: utf-8 -*-

"""
Rewrite the <env-tasks> block of mise.toml from the entries of StackCtxEnum,
the members of EnvNameEnum, and the config of each environment.
"""

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import path_enum
from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.mise_tasks import (
    render_project_env_tasks,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.mise_tasks import (
    update_mise_toml,
)


def main():
    changed = update_mise_toml(
        path=path_enum.path_mise_toml,
        block=render_project_env_tasks(),
    )
    if changed:
        print(f"Updated {path_enum.path_mise_toml}")
    else:
        print(f"{path_enum.path_mise_toml} is already up to date")


if __name__ == "__main__":
    main()
