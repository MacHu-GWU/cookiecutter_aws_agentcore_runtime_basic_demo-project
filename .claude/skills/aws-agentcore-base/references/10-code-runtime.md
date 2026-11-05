---
description: "OP-1 Code Runtime: the four places the project's code runs (local, agentcore_local, ci, agentcore), the signals that tell them apart and who sets each, the detection order, how other code asks for the runtime, how it is tested, and how to change it. Read before writing code that behaves differently by where it runs, when a runtime is detected wrongly, or before adding a runtime kind."
---

# Code Runtime

Implements **OP-1**.

| | |
| :--- | :--- |
| EP | `<package_name>/runtime.py` |
| FP | `<package_name>/constants.py` (the signals), `<package_name>/runtime.py`, `tests/test_runtime.py`, the autouse fixture of `tests/conftest.py` that forces `local` |
| CMD | `mise run cov`; one module: `.venv/bin/python tests/test_runtime.py` |

---

## 1. What a runtime is

The **runtime** is where the code is running. It is independent of the **environment** (`dev`, `tst`, `prd`), which is what the code targets: a `local` run can target `prd`, and a `dev` deploy runs on `agentcore`.

The same code runs in four runtimes:

| Runtime | What runs | Started by | Typical use |
| :--- | :--- | :--- | :--- |
| `local` | the package from the repo, in the repo's `.venv` | a developer: tests, scripts, local servers | write and test the code |
| `agentcore_local` | the packaged copy of a runtime in `app/<Runtime>/`, in its own `.venv` | `agentcore dev`, the AgentCore CLI's local simulation | check the packaging and the cloud code path on a dev machine, with local AWS credentials |
| `ci` | the package from the repo | a CI runner, such as GitHub Actions | tests, which run as `local` (section 5); loading the config is not supported here (`20-centralized-config.md`) |
| `agentcore` | the packaged copy, in an AgentCore microVM | AgentCore Runtime | the deployed runtime |

The code needs to know which one it is in to choose its dependencies: where the config comes from, which AWS credentials and region to use. That choice is made in one place per dependency; this OP only answers "where am I".

---

## 2. The signals

| Signal | Constant in `constants.py` | Set by | Counts when |
| :--- | :--- | :--- | :--- |
| `IS_AGENTCORE_RUNTIME` | `IS_AGENTCORE_RUNTIME_VAR`, value `IS_AGENTCORE_RUNTIME_VALUE` | the project, through `envVars` of every runtime in `agentcore.json` (generated); `agentcore dev` applies `envVars` too | its value is exactly `true` |
| `LOCAL_DEV` | `AGENTCORE_DEV_VAR` | `agentcore dev`, on the server it runs (`LOCAL_DEV=1`) | it is present, whatever its value |
| `CI` | `CI_VAR` | GitHub Actions and most CI services, on every runner | it is present, whatever its value |

Why these:

- **AgentCore sets no variable that says "you run on AgentCore"** (none in the docs, look it up again with `00-agentcore-docs-mcp.md` before relying on that). So the project sets its own, `IS_AGENTCORE_RUNTIME`, in the one file every runtime gets its environment from. The code that writes it uses the same two constants, so writer and reader cannot drift.
- **`agentcore_local` and `agentcore` run the same packaged code with the same `envVars`.** The only difference the code can see is `LOCAL_DEV`, set by `agentcore dev` and never by AgentCore Runtime. This is **undocumented CLI behavior** (AgentCore CLI 1.0.1, `commandForRuntime` in the CLI's source): check it again after every CLI upgrade.
- `LOCAL_DEV` alone, or `IS_AGENTCORE_RUNTIME` with any value but `true`, means nothing.

---

## 3. The detection order

`Runtime.get_current_runtime_name()`:

```text
IS_AGENTCORE_RUNTIME == "true" ?
├── yes: LOCAL_DEV present ?
│        ├── yes → agentcore_local
│        └── no  → agentcore
└── no:  CI present ?
         ├── yes → ci
         └── no  → local
```

The project's own signal comes first, so an AgentCore runtime is never taken for `ci` or `local`, whatever else the environment holds.

---

## 4. Asking for the runtime

- Ask `one.runtime.current_runtime_name()` (or the `runtime` singleton of `runtime.py`); it returns a string such as `"agentcore_local"`. Compare it with `RuntimeNameEnum.<name>.value`.
- Never read the signals anywhere but `runtime.py`, and never write their names or the value `true` anywhere but `constants.py`.
- Branch one runtime at a time, so each runtime's behavior reads on its own (the general rule of the `pywf-aws-cdk-base` skill, reference *Runtime*).
- Only the code that builds dependencies asks. Business code never does: it receives its dependencies already chosen, which is what lets the same function run in every runtime.
- Importing `runtime.py` does nothing, and the answer is worked out again on every call, never cached: a test, or a process that changes its environment, gets the current answer.

---

## 5. Tests

`tests/test_runtime.py`:

- One parametrized case per combination of signals, including the edge cases: an empty `CI` or `LOCAL_DEV` still counts, `True` or `false` for `IS_AGENTCORE_RUNTIME` does not, `LOCAL_DEV` alone does not, an AgentCore runtime wins over `CI`.
- The answer is not cached.
- The signal names are written out in the test, not imported from `constants.py`: they are a contract with `agentcore.json` and the CLI, so renaming a constant's value must fail a test.

`tests/conftest.py` removes the three signals and sets `ENV_NAME=dev` for every test, so the suite runs as `local` everywhere, a CI runner included. It also removes the `AWS_PROFILE_FOR_<ENV>` profiles mise loads from `.env`, so no test signs in to a real account by accident.

---

## 6. Changing it

- **A new runtime kind** (a container, a Lambda function): a member of `RuntimeNameEnum`, its signal in `constants.py` with who sets it, its place in the order of section 3, a test case per combination. Then every branch on the runtime must handle it or raise `NotImplementedError`.
- **After upgrading the AgentCore CLI**: run `agentcore dev` and check its server still gets `LOCAL_DEV`; if not, find what tells it apart now, and change `AGENTCORE_DEV_VAR` and this file together.
