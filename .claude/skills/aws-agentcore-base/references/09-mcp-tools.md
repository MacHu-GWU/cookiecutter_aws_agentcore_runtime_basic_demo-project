---
description: "How an MCP runtime and its tools are written here: business functions that take the engine and return Pydantic models, separate from the SQLAlchemy ORM; thin FastMCP tools that call them with one.engine and copy their docstrings; the engine as a per-process singleton; the FastMCP settings AgentCore requires. Read before adding or changing an MCP tool, a query, an ORM model, or a result model, or when writing a new MCP runtime."
---

# MCP Runtimes and Tools

Code: `<pkg>/runtimes/power_plant_mcp.py` (the runtime), `<pkg>/power_plant/` (the business logic).

---

## 1. Three layers

| Layer | Module | Knows about |
| :--- | :--- | :--- |
| Storage | `power_plant/orm.py`: SQLAlchemy models, relationships, `create_db_engine`, `load_seed_data` | the database |
| Business | `power_plant/queries.py`: one function per question; `power_plant/schemas.py`: Pydantic result models | an engine passed in; no config, no `one`, no MCP |
| Runtime | `runtimes/power_plant_mcp.py`: FastMCP server, one tool per query | `one.engine`, MCP |

The business layer is unit tested with its own in-memory engine (`tests/power_plant/`); the runtime layer only wires it up.

---

## 2. Results are Pydantic models, not ORM rows or dicts

A table and an answer are different things even when they share fields: an answer may leave out columns, add related rows, or reshape values, and the database may change without changing the tool's contract. So each query returns a model from `schemas.py`:

- `model_config = ConfigDict(from_attributes=True)`, so `SiteDetail.model_validate(orm_row)` builds it from a row, related rows included (through the ORM relationships, read while the session is open).
- Every field has `Field(description=...)`. FastMCP turns the return type into the tool's output schema, so these descriptions are what the LLM reads about each field.
- Fields one per line, fenced by `# fmt: off` / `# fmt: on` (project rule).

FastMCP returns a model both as JSON text and as structured output. A `list[...]` result is wrapped as `{"result": [...]}` in the structured output.

---

## 3. A tool is a thin wrapper

```python
@mcp.tool()
@_doc_from(queries.get_site)
def get_site(site_id: str) -> SiteDetail:
    return queries.get_site(one.engine, site_id=site_id)
```

- The tool does not take the engine, so the LLM never sees it. (`functools.wraps` would not do: it exposes the wrapped signature, engine included.)
- `_doc_from` copies the query's docstring, which becomes the tool description. Write the first paragraph of a query's docstring for the LLM, and do not mention the engine in it.
- Errors: raise `ValueError` with a clear message (`site 'S-99' not found`); FastMCP returns it to the client as a tool error.
- `test_list_tools` checks every tool: description = query docstring, no `engine` parameter, an output schema.

---

## 4. The engine

`one.engine` (`one/one_05_db.py`) is created once per process on first use, from `config.db_connection_string`, with the seed data loaded.

- **One per process** is one per runtime session: each session has its own microVM and process (`02`). Nothing is shared across sessions.
- With a real database, every session holds its own connection pool, so total connections = sessions × pool size. Keep the pool small, or put RDS Proxy in front.
- The demo database is in-memory SQLite (`sqlite+pysqlite:///:memory:`): `create_db_engine` gives it `StaticPool` and `check_same_thread=False`, so every connection, from any of the server's worker threads, sees the same database. `load_seed_data` is idempotent (`merge` by primary key).
- `db_connection_string` is in `config-<env>-secret.json5`: a real one holds a password.

---

## 5. FastMCP settings AgentCore requires

```python
mcp = FastMCP(
    "<Name>",
    host="0.0.0.0",
    port=int(os.environ.get("FASTMCP_PORT", "8000")),
    stateless_http=True,
)
...
mcp.run(transport="streamable-http")
```

- Port 8000, path `/mcp`, streamable HTTP: the MCP protocol contract of AgentCore Runtime.
- `FASTMCP_PORT` lets the local tasks and `agentcore dev` move it (`10`); deployed, it is unset, so 8000.
- `stateless_http=True`: no server-side MCP session state. AgentCore still routes by `Mcp-Session-Id` to the same microVM (`02`).
- `main()` loads the config and the engine before `mcp.run(...)` (`06`, section 5).
