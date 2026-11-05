# -*- coding: utf-8 -*-

"""
Call a local MCP server: list its tools, then call one.
``ac-local-mcp-call.py --url <url> --tool <name> --arguments <json>``.
"""

import sys

from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.mcp_client import main


if __name__ == "__main__":
    sys.exit(main())
