# -*- coding: utf-8 -*-

"""
Exit 0 only if the user answers y or yes:
``confirm.py --action <text> [--skip_var <VAR> ...]``.
"""

import sys

from cookiecutter_aws_agentcore_runtime_basic_demo.confirm import main


if __name__ == "__main__":
    sys.exit(main())
