# -*- coding: utf-8 -*-

"""
Thin entry points of the AgentCore Runtimes. They glue the pure business code in
``power_plant`` to the runtime frameworks (mcp, strands), and never import config,
``one``, or cdk, because they are copied into the runtime zips.
"""
