# -*- coding: utf-8 -*-

"""
Free a local TCP port held by a leftover dev server of this project:
``free-port.py --port <port>``.
"""

import sys

from cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_port import (
    main,
)


if __name__ == "__main__":
    sys.exit(main())
