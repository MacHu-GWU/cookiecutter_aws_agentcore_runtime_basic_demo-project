# -*- coding: utf-8 -*-

"""
The runtime modules: one per AgentCore Runtime, ``<runtime_name>.py`` (or a
subpackage with a ``main.py`` when it grows), each with a ``main()`` that serves.

A runtime module is the thin layer between the business functions and a runtime
framework (FastMCP, Strands): it registers the functions, injects their
dependencies from ``one``, and loads the config at startup. The business
functions it wraps never import ``one``, the config, or a framework. Everything
here is copied into the runtime zips, so it imports at module level only the
standard library, the ``agentcore`` dependency group, and other copied code.
"""
