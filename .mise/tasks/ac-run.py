# -*- coding: utf-8 -*-

"""
Run a runtime of the registry locally, or call it:
``ac-run.py --runtime <Name> --mode local|dev|call``.
"""

import sys

from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_run import main


if __name__ == "__main__":
    sys.exit(main())
