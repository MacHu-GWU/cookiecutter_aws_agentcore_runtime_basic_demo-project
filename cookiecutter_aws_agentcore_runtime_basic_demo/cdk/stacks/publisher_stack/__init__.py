# -*- coding: utf-8 -*-

"""
The publisher stack, the folder form of a stack: ``stack.py`` holds the class,
and each ``stack_0N_<topic>.py`` mixin one group of resources. It holds an IAM
role allowed to publish to the alert topic of the alerts stack, and an SSM
parameter with the topic ARN.
"""
