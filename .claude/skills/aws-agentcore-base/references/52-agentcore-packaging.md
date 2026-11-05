---
description: "OP-5 AgentCore Runtime, layer 3: how each runtime is packaged as a CodeZip: the code directory app/<Runtime>/ with its main.py shim, its pinned pyproject.toml, and the copy of the package; the import rule copied code follows; how the AgentCore CLI installs dependencies (wheels only, Linux aarch64) and how ac-check-wheels checks it; and ac-build. Read before adding a dependency or a module a runtime imports, when a runtime fails to import, or when agentcore deploy fails with 'uv install failed for all platform candidates'."
---

# Packaging a Runtime

Implements **OP-5**, layer 3.

| | |
| :--- | :--- |
| EP | `<package_name>/agentcore_project/codezip.py` (called by `ac-gen`, `51-agentcore-config.md`) |
| FP | `<package_name>/agentcore_project/codezip.py`, `[dependency-groups] agentcore` of `pyproject.toml`, `uv.lock`, `.mise/tasks/ac-check-wheels.py`, `tests/agentcore_project/test_agentcore_project_codezip.py` |
| CMD | `mise run ac-gen`, `mise run ac-check-wheels`, `mise run ac-build` (none calls AWS) |

---

## 1. What `app/<Runtime>/` holds

Build type `CodeZip`, Python `RUNTIME_PYTHON`. `assemble_runtime_dir` writes three things into each runtime's code directory and leaves everything else there alone (the `.venv` and `uv.lock` that `agentcore dev` makes, so a running dev server keeps working):

| File | Content | Why |
| :--- | :--- | :--- |
| `main.py` | a generated shim: `from <package_name>.<module> import main`, plus `app` for an `HTTP` runtime, and `main()` under `if __name__ == "__main__"` | AgentCore runs `python main.py`; `agentcore dev` serves an `HTTP` runtime with `uvicorn main:app --reload`, where calling `main()` at import would fail (an event loop is already running) |
| `pyproject.toml` | `[project].dependencies` = the `agentcore` dependency group with every transitive dependency, pinned: `uv export --frozen --only-group agentcore` (`export_requirements`, `render_pyproject_toml`) | the CLI installs only `[project].dependencies` and ignores `uv.lock`, so the lock is applied by pinning every version |
| `<package_name>/` | a fresh copy of `RUNTIME_MODULES` (`__init__.py`, `constants.py`, `env.py`, `paths.py`, `runtime.py`) and `RUNTIME_SUBPACKAGES` (the config, `one`, the business subpackages, `runtimes`) | the runtime runs the same code as the repo |

Never copied: `cdk/`, `agentcore_project/`, `devtools/`: they run on the dev machine only. The copy lists are global: every runtime gets the same code, one zip shape for all.

---

## 2. The import rule

**Copied code imports, at module level, only the standard library, the `agentcore` dependency group, and other copied code.** Anything dev-only is imported inside the function that needs it, such as `json5` in `Config.load_from_local_config_file`, and `aws_cdk` and the stacks in the properties of `one/one_03_cdk.py`.

`test_assemble_runtime_dir` checks it: it assembles a runtime, then imports every runtime module and `one` from the copy, in a subprocess where `aws_cdk`, `cdk_mate`, and `json5` raise `ImportError`, and checks that only copied modules were loaded.

A new business subpackage that a runtime imports goes into `RUNTIME_SUBPACKAGES`, and into the `allowed` list of that test.

---

## 3. How the CLI installs the dependencies

At synth time (`agentcore build` or `deploy`), `@aws/agentcore-cdk` runs, per runtime:

```text
uv pip install -r pyproject.toml --target <staging> --python-version 3.12
    --python-platform <platform> --only-binary :all:
```

for `aarch64-manylinux2014`, then `_2_28`, then `_2_34` (`CODEZIP_PLATFORMS`), and keeps the first that works. **Wheels only, Linux aarch64.** A package version with no such wheel cannot be installed, and the CLI then reports only "uv install failed for all platform candidates". Both are undocumented CLI behavior (1.0.1, `PLATFORM_CANDIDATES` in `lib/packaging/python.js`): check them again after a CLI upgrade.

**`ac-check-wheels`** runs the same command as a dry run for every runtime in `app/` (`check_codezip_install`, `check_codezip_installs`), and keeps uv's own message, which names the package:

```bash
mise run ac-check-wheels
```

`ac-deploy-<env>` runs it before deploying.

**The fix** for a version without a wheel: constrain it out in `pyproject.toml` with a comment (an upper bound, or `!=<version>`), then `uv lock`. A release can reach PyPI before its wheels do (SQLAlchemy 2.1.7 was an sdist only for a while, which failed a deploy: hence `sqlalchemy<2.1.0`). A package with no aarch64 wheel at all cannot be used in a CodeZip runtime; use a container build instead.

**A new dependency** of a runtime: add it to `[dependency-groups] agentcore` only, `uv lock`, `mise run ac-check-wheels`. The dev machine gets it too: `mise run inst` installs every group. The base dependencies are what the code that is never copied needs (CDK, the config loader).

---

## 4. Size

A runtime zip is about 44 MB, almost all of it the `agentcore` group (Strands, OpenTelemetry, boto3); the code copy is small. Keep the group to what the runtimes import: a smaller zip also starts faster.

---

## 5. Build

```bash
mise run ac-build
```

`agentcore build` after `ac-gen`: installs each runtime's dependencies as above, zips it, and synthesizes the AgentCore stack of the target. No AWS call. It is the last local check of a deploy.

---

## 6. Tests

`tests/agentcore_project/test_agentcore_project_codezip.py`: the exported requirements are the pinned `agentcore` group only; the rendered `pyproject.toml`; `assemble_runtime_dir` (stale code replaced, `.venv` kept, the shim of each protocol, no dev tooling copied, the import rule); `check_codezip_install` with the real lock and with a version that cannot install; `check_codezip_installs`.

```bash
.venv/bin/python tests/agentcore_project/test_agentcore_project_codezip.py
```
