# -*- coding: utf-8 -*-

"""
Exit 1 unless the dependencies of every runtime in app/ (run ac-gen first)
install as agentcore deploy installs them: wheels only, for Linux aarch64.
"""

import sys

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import path_enum
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.runtime_dir import (
    check_codezip_install,
)


def main() -> int:
    code = 0
    for path in sorted(path_enum.dir_agentcore_app.glob("*/pyproject.toml")):
        error = check_codezip_install(path)
        if error is None:
            print(
                f"OK: the dependencies of {path.parent.name} have Linux aarch64 wheels"
            )
        else:
            print(f"ERROR: the dependencies of {path.parent.name} do not install:")
            print(error)
            code = 1
    return code


if __name__ == "__main__":
    sys.exit(main())
