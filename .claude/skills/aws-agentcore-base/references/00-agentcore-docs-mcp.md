---
description: "How to look up the official AgentCore docs live through the AgentCore MCP server of the project's .mcp.json, which of its tools are safe to call, and what to do when they are missing. Read before answering any AgentCore question or relying on an AgentCore behavior, or when the AgentCore doc tools are missing."
---

# AgentCore Docs Through MCP

Not an OP of its own: a habit of every OP. AgentCore changes fast, so its behavior is looked up, never answered from memory.

---

## 1. What is set up

The project's `.mcp.json` registers the AgentCore MCP server as `bedrock-agentcore-mcp-server` (`uvx awslabs.amazon-bedrock-agentcore-mcp-server@latest`), following the official guide *AgentCore MCP Server: Vibe coding with your coding assistant* (`mcp-getting-started.md`). Two doc tools are auto-approved:

| Tool | Does |
| :--- | :--- |
| `search_agentcore_docs` | searches the official docs; returns URLs, titles, snippets |
| `fetch_agentcore_doc` | fetches the whole page of a URL from a search |

---

## 2. How to use it

- Search first, then fetch the page that answers the question. Cite the page name (such as `runtime-service-contract.md`) when a decision rests on it.
- The `get_*_guide` tools (such as `get_runtime_guide`) only read docs too, and are fine to call.
- When the docs and this project disagree: the docs win on what the service supports, the project wins on how things are done here. Tell the user about the gap.
- A behavior the docs do not state, such as one read from the AgentCore CLI's source, is recorded as undocumented where the code relies on it, so it is checked again after a CLI upgrade.

---

## 3. What not to use it for

The same server has tools that create, change, or delete AWS resources or start live sessions (such as `create_agent_runtime`, `gateway_create`, `memory_create`, `start_browser_session`). They act with the server process's own credentials, not the per-environment session of this project, and bypass its deploy tasks. Never call them unless the user names the call and says yes.

---

## 4. When the tools are missing

The server is still connecting, or failed to start: check that `uvx` is installed and that the server is enabled (`/mcp` in an interactive `claude` terminal). Meanwhile, read the pages under `https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/` directly.
