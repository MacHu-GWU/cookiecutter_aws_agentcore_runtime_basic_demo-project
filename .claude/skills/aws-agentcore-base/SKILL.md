---
name: aws-agentcore-base
description: "Shared knowledge of the aws-agentcore skills: the best practices this repo has settled on for building multi-environment AWS Bedrock AgentCore projects, mainly AgentCore Runtime hosting either an agent or an MCP server. Includes how to look up the official AgentCore docs through the AgentCore MCP server. Load it before working on or answering a question about AgentCore in this project."
---

The best practices this repo has settled on for AgentCore projects: a multi-environment scaffold centered on AgentCore Runtime, which can host an agent or an MCP server. This skill holds the decisions; the official docs are looked up live (see `01`).

For the project's general AWS and CDK conventions (config, environments, boto session, stacks), use the `pywf-aws-cdk-base` skill. This skill covers only what is specific to AgentCore.

## References

For a question, read only the file that covers it.

- **AgentCore Docs Through MCP** (`references/01-agentcore-docs-mcp.md`): Read before answering any AgentCore question, or when the AgentCore doc tools are missing.

## Invokers

None yet. Each future `aws-agentcore-<action>` skill loads this one and lists here which references it reads.
