# -*- coding: utf-8 -*-

"""
Exit 1 unless the dependencies of every runtime in app/ (run ac-gen first)
install as agentcore deploy installs them: wheels only, for Linux aarch64.
"""

import sys

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import path_enum
from cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.codezip import (
    check_codezip_installs,
)


if __name__ == "__main__":
    sys.exit(0 if check_codezip_installs(path_enum.dir_agentcore_app) else 1)
