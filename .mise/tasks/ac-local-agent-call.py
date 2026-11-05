# -*- coding: utf-8 -*-

"""
Call a local agent server: ``ac-local-agent-call.py --url <url> --prompt <text>
[--session-id <id>]``.
"""

import sys

from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.agent_client import main


if __name__ == "__main__":
    sys.exit(main())
