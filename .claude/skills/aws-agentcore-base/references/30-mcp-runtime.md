---
description: "OP-3 MCP Runtime, in three layers, each with its own files, tests, and commands: tool functions as pure business functions with injected dependencies and Pydantic results; the thin FastMCP server in <package_name>/runtimes/ that registers them with the AgentCore settings; running and calling it locally on its own port. Read before writing or changing an MCP tool, its business function or result model, or an MCP runtime module, or before running or calling an MCP server locally."
---

# MCP Runtime

Implements **OP-3**. Packaging and deploying it are later OPs; this file stops at a server that runs and answers locally.

| | |
| :--- | :--- |
| EP | `<package_name>/runtimes/<runtime_name>.py`, or `<package_name>/runtimes/<runtime_name>/main.py` |
| FP | layer 1: `<package_name>/<domain>/**`, `tests/<domain>/**`; layer 2: the runtime module, `<package_name>/runtimes/common.py`, the dependency's `one` mixin, `tests/runtimes/**`; layer 3: `<package_name>/devtools/**`, `.mise/tasks/{free-port,ac-run}.py`, the generated `ac-local-<slug>*` tasks, `tests/devtools/**` |
| CMD | per layer, in each section; all: `mise run cov` |

---

## 1. A tool is a function

An MCP server is a set of tools, and a tool is a function. The code is split so that the function can be written and tested with nothing else around it:

| Layer | What | Knows about | Tested with |
| :--- | :--- | :--- | :--- |
| 1. Tool functions | business functions and their result models | only their arguments | their own local dependencies (an in-memory database, a stub client) |
| 2. MCP server | the runtime module: registers each function as a tool, injects its dependencies, `main()` | layer 1, FastMCP, `one` | the server object in memory; a real local server |
| 3. Local run | the server on a local port, a client to call it | layer 2 | by hand, and the client's tests against a real local server |

The rule underneath: **a business function is stateless, and everything outside it (an engine, an AWS client, the config) is an argument.** Only layer 2 builds those dependencies, for the runtime it is in, so the same function runs in a test, on a laptop, and on AgentCore.

---

## 2. Layer 1: the tool functions

**Where:** wherever the business fits, usually a subpackage named after it, `<package_name>/<domain>/`. The template fixes no place. Typical modules:

| Module | Holds |
| :--- | :--- |
| `<domain>/queries.py` (or any name) | one function per question the tool answers |
| `<domain>/schemas.py` | the Pydantic result models: the tools' contract |
| `<domain>/orm.py`, `<domain>/data.py` | storage models and seed data, for a database |

**A function:**

```python
def get_order(engine: sa.Engine, order_id: str) -> OrderDetail:
    """
    Get one order with its lines.

    :raises ValueError: if the order does not exist.
    """
    with orm.Session(engine) as session:
        order = session.get(Order, order_id)
        if order is None:
            raise ValueError(f"order {order_id!r} not found")
        return OrderDetail.model_validate(order)
```

- **Dependencies first, as arguments**: the engine, a client. Never `one`, the config, or the MCP framework.
- **The first paragraph of the docstring is the tool description the LLM reads.** Write it for the LLM; never mention the injected dependency.
- **Returns a contract model, not a storage row or a dict.** A table and an answer differ even when they share fields: the answer may leave out columns, add related rows, or reshape values, and the storage may change without changing the contract.
- **Errors are `ValueError`** with a message the LLM can act on; the server turns it into a tool error.

**A result model:** a Pydantic `BaseModel`, `model_config = ConfigDict(from_attributes=True)` so `Model.model_validate(row)` builds it from a storage row (related rows included, read while the session is open), and `Field(description=...)` on every field. The server turns the return type into the tool's output schema, so these descriptions are what the LLM reads about each field.

**The import rule:** this code is copied into the runtime zip, so it imports at module level only the standard library and the `agentcore` dependency group.

**Tests and CMD:** `tests/<domain>/test_<domain>_<module>.py`, each with its own fixtures, such as a seeded in-memory engine; nothing from `one`.

```bash
.venv/bin/python tests/<domain>/test_<domain>_<module>.py
```

---

## 3. Layer 2: the MCP server

**Where:** always `<package_name>/runtimes/`, one runtime module per MCP runtime: `<runtime_name>.py`, or a subpackage `<runtime_name>/` with its entry in `main.py` when it grows. Either way it has a `main()`.

```python
from ..one.api import one
from ..<domain> import queries
from ..<domain>.schemas import OrderDetail
from .common import new_mcp_server, run_mcp_server, doc_from, print_config_source

mcp = new_mcp_server("<Runtime>")


@mcp.tool()
@doc_from(queries.get_order)
def get_order(order_id: str) -> OrderDetail:
    return queries.get_order(one.engine, order_id=order_id)


def main():
    print_config_source()
    print(f"Connected to the database {one.engine.url!r}", flush=True)
    run_mcp_server(mcp)
```

(One imported name per line in real code.)

- **One thin wrapper per tool**: the signature without the dependency, the business function's docstring through `doc_from` (`functools.wraps` would copy the signature too, and expose the dependency), the dependency taken from `one`, the result model as the return type.
- **The server name** is the runtime's name in `agentcore.json` (`agentcore_runtime_name_<x>` of the config); a test checks they match.
- **The dependency** is a `one` property (`one/one_0N_<topic>.py`), built on first use and kept for the process. On AgentCore one process serves one runtime session, so it is one per session: with a real database, total connections are sessions × pool size, so keep the pool small or put a proxy in front.
- **What a client gets**: the result as JSON text and as structured output; a `list[...]` result is wrapped as `{"result": [...]}` in the structured output. A `ValueError` becomes a tool error with its message.
- **`main()`** loads the config (and the dependencies) and prints where they came from, flushed, before serving: a runtime that cannot start fails before taking traffic, with the reason in its log.

**`runtimes/common.py`**, shared by every runtime module:

| Name | What |
| :--- | :--- |
| `new_mcp_server(name)` | a FastMCP server with the AgentCore MCP contract: host `0.0.0.0`, port from `FASTMCP_PORT` (default 8000), path `/mcp`, `stateless_http=True` (AgentCore still keeps a client on one microVM through its `Mcp-Session-Id`) |
| `run_mcp_server(mcp)` | serve over `streamable-http`, blocking |
| `doc_from(func)` | give a tool the docstring of `func` |
| `print_config_source()` | load the config; print its environment and the runtime |
| `MCP_PORT_VAR`, `MCP_DEFAULT_PORT`, `MCP_PATH`, `MCP_TRANSPORT` | the contract as constants |

**Tests and CMD:** `tests/runtimes/test_runtimes_<runtime_name>.py` checks the server name; the tool list; for each tool: description = the business function's docstring, no dependency in the input schema, an output schema; a call per tool through `mcp.call_tool` (in memory, through `one`); a not-found error; `main()` with `mcp.run` stubbed. `tests/runtimes/test_runtimes_common.py` checks the shared settings.

```bash
.venv/bin/python tests/runtimes/test_runtimes_<runtime_name>.py
.venv/bin/python tests/runtimes/test_runtimes_common.py
```

---

## 4. Layer 3: run and call it locally

Every runtime has, from its entry in the runtime registry (`<package_name>/agentcore_project/registry.py`), a local port and a sample payload, and three generated tasks, named after its slug (`MyMcp` → `my-mcp`). All three run `.venv/bin/python .mise/tasks/ac-run.py --runtime <Runtime> --mode <mode>`, which is `<package_name>/devtools/local_run.py`: no per-runtime command is written by hand.

**Run:**

```bash
mise run ac-local-<slug>
```

It frees the runtime's local port, then runs `FASTMCP_PORT=<port> .venv/bin/python -m <package_name>.runtimes.<runtime_name>` (printing both first): the package from the repo, runtime `local`, config from the files, no AWS needed unless a tool calls AWS.

**Ports:** each runtime has its own unusual local port in the registry (18731, then the next number), below the ephemeral range (32768+), so a listener there is almost surely a leftover server of this repo, and no outgoing connection takes it by chance. A test checks they are unique. Deployed runtimes always listen on AgentCore's 8000; no deploy code knows the local ports.

**`free-port`** (`<package_name>/devtools/local_port.py`, also `mise run free-port --port <port>`): the run tasks call it first.

- A listener counts as this repo's when its working directory is inside the repo root.
- If any listener is not this repo's (another clone or worktree included), nothing is stopped: it prints each pid and command line and exits 1.
- Otherwise `SIGTERM`, a 5 s wait, then `SIGKILL` for what still listens. The terminal whose server was stopped prints `ERROR task failed`: expected.
- It uses `lsof`, which sees only the current user's processes.

**Call:**

```bash
mise run ac-local-<slug>-call
```

It sends the runtime's sample payload (a JSON-RPC `tools/call` request: the tool and its arguments) through `<package_name>/devtools/mcp_client.py` to `http://localhost:<port>/mcp`: it prints the tool names, then the tool's result as JSON, or the tool error (exit 1). Another tool by hand:

```bash
.venv/bin/python -c "from <package_name>.devtools.mcp_client import main; main()" --url http://localhost:<port>/mcp --tool <name> --arguments '<json>'
```

As a library: `list_tools(url)`, `call_tool(url, name, arguments)`; both take an `auth`, used to call a deployed runtime.

**Tests and CMD:** `tests/devtools/test_devtools_mcp_client.py` runs the client against the real server, served on a free port by the session fixture `mcp_url` of `tests/conftest.py`; `tests/devtools/test_devtools_local_port.py` starts and stops real listeners; `tests/devtools/test_devtools_local_run.py` checks every command and environment `local_run` builds.

```bash
.venv/bin/python tests/devtools/test_devtools_mcp_client.py
.venv/bin/python tests/devtools/test_devtools_local_port.py
.venv/bin/python tests/devtools/test_devtools_local_run.py
```

`<package_name>/devtools/` is dev-machine tooling: never copied into a runtime zip.

---

## 5. Adding an MCP runtime, this OP's part

1. Layer 1: the business functions and result models in `<package_name>/<domain>/`, with their tests.
2. A dependency the tools need: a `one` property in its own `one/one_0N_<topic>.py`, with its test; its connection settings in the config.
3. Layer 2: `<package_name>/runtimes/<runtime_name>.py` as in section 3, and `tests/runtimes/test_runtimes_<runtime_name>.py`.
4. Layer 3: an entry in the runtime registry with the next free local port and a sample `tools/call` payload, then `mise run gen-env-tasks` for its `ac-local-<slug>` tasks.
5. `mise run cov`, then run and call it.

Its names in the config are OP-2 (`20-centralized-config.md`, section 5); packaging and deploying it are later OPs.
