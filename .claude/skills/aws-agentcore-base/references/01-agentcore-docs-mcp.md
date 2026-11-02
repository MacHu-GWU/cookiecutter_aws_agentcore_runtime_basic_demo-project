---
description: "The AgentCore MCP server configured in the project's .mcp.json, and how to use it to look up the official AgentCore docs on demand instead of answering from memory. Read before answering any AgentCore question, or when the AgentCore doc tools are missing."
---

# AgentCore Docs Through MCP

---

## 1. What is set up

Following the official guide [AgentCore MCP Server: Vibe coding with your coding assistant](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/mcp-getting-started.html), the project's `.mcp.json` registers the AgentCore MCP server as `bedrock-agentcore-mcp-server` (run with `uvx awslabs.amazon-bedrock-agentcore-mcp-server@latest`). Its two doc tools are auto-approved there:

- `search_agentcore_docs`: search the official AgentCore docs; returns URLs, titles, and snippets.
- `fetch_agentcore_doc`: fetch the full page of a URL from that search.

In short: the official docs are looked up live, never answered from memory.

---

## 2. How to use it

- For any AgentCore question (Runtime, Memory, Gateway, Identity, Policy, Observability, the APIs), search first, then fetch the page that answers it. AgentCore changes fast; training knowledge is likely out of date.
- The `get_*_guide` tools (such as `get_runtime_guide`) also only read docs and are fine to call.
- When the docs and this repo disagree, this repo's decisions win for how things are done here; the docs win for what the service supports. Tell the user about the gap.

---

## 3. What not to use it for

The same server also has tools that create, change, or delete AWS resources and start live sessions (such as `create_agent_runtime`, `gateway_create`, `memory_create`, `start_browser_session`). They act with whatever AWS credentials the server process has, not the per-environment boto session of this repo, and this repo deploys its resources through CDK. Do not call them unless the user asks for that call by name and says yes.

---

## 4. If the tools are missing

The server is still connecting, or it failed to start. Check that `uvx` is installed and that the server is enabled (`/mcp` in an interactive `claude` terminal). Until it works, fall back to fetching the docs pages under `https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/` directly.
