Seed Repo Release and Version History
==============================================================================
The changelog of this **seed repo** itself. The seed is a runnable project that `cookiecutter-aws_agentcore_runtime_basic <https://github.com/MacHu-GWU/cookiecutter-aws_agentcore_runtime_basic>`_ (the template repo) turns into a cookiecutter template, so every change here is a change to what newly generated projects get.

- The seed and the template repo share one version number. The source is ``version`` in this repo's ``pyproject.toml``; the template repo copies it and refuses to publish when the two differ.
- ``release-history.rst`` is template content: the starting changelog of every generated project. It never records the seed's own changes, and is never edited for a seed release.
- This file is excluded from the template. Each template release links to its section here.


x.y.z (Backlog)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

**Minor Improvements**

**Bugfixes**

**Miscellaneous**


1.0.0 (2026-11-05)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Features and Improvements**

- First release of the seed for multi-environment AWS Bedrock AgentCore Runtime projects: runtimes written local first as plain Python, deployed per environment by the AgentCore CLI, with the resources they depend on in a Python CDK ``agentcore_deps`` stack.
- Generated projects start with two example runtimes that work together, both on a small power plant database (sites, assets, technicians):
  - ``PowerPlantMcp``, an MCP server runtime (FastMCP) with the read-only tools ``list_sites``, ``list_assets``, ``get_site``, and ``get_technician``.
  - ``SiteAgent``, an agent runtime (Strands on a Bedrock model) that calls ``PowerPlantMcp`` over MCP and has its own ``get_weather`` tool, to answer questions such as whether a site can be inspected tomorrow.
- One runtime registry declares every runtime; ``mise run gen-env-tasks`` derives from it the per environment tasks (``ac-deploy-<env>``, ``ac-down-<env>``, ``ac-status-<env>``, ``ac-chain-up-<env>``, ``ac-chain-down-<env>``, ``ac-test-<env>``) and the per runtime tasks to run, call, invoke, and read the logs of each runtime, locally and deployed.
- Add the AgentCore skill family for Claude Code: ``aws-agentcore-base`` (one reference per operation, from the code runtime and config to deploy, teardown, invoke and observe, and maintenance), and the invokers ``aws-agentcore-new-mcp``, ``aws-agentcore-new-agent``, ``aws-agentcore-change-mcp``, ``aws-agentcore-change-agent``, ``aws-agentcore-deploy``, and ``aws-agentcore-debug``.
