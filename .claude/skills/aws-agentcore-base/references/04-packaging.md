---
description: "How a runtime's code directory app/<Runtime>/ is assembled from the package and uv.lock, which modules are copied, the import rule the copied code must follow, and how the CLI installs dependencies (wheels only, Linux aarch64). Read before adding a dependency or a module a runtime imports, when a runtime fails to import, or when agentcore deploy fails with 'uv install failed for all platform candidates'."
---

# Packaging a Runtime

Code: `<pkg>/agentcore_project/runtime_dir.py`. Build type: `CodeZip`, Python 3.12 (`RUNTIME_PYTHON`).

---

## 1. What `app/<Runtime>/` holds

`ac-gen` writes three things into each runtime's `codeLocation`, and leaves everything else there alone (the `.venv` and `uv.lock` of `agentcore dev`, so a running dev server keeps working):

| File | Content |
| :--- | :--- |
| `main.py` | a generated shim: `from <pkg>.<module> import main` (plus `app` for an HTTP runtime), and `main()` under `if __name__ == "__main__"` |
| `pyproject.toml` | `[project].dependencies` = the `agentcore` dependency group with every transitive dependency, pinned: `uv export --frozen --only-group agentcore` |
| `<pkg>/` | a fresh copy of only what the runtimes need (section 2) |

Why a shim that exposes `app`: AgentCore runs `python main.py`, but `agentcore dev` serves an HTTP runtime with `uvicorn main:app --reload`. Calling `main()` at import time fails there ("asyncio.run() cannot be called from a running event loop").

Why a pinned export: the CLI installs only `[project].dependencies` and ignores `uv.lock`, so the lock is applied by pinning every version in the generated file.

---

## 2. What is copied, and the import rule

`RUNTIME_MODULES` (`__init__.py`, `constants.py`, `env.py`, `paths.py`, `runtime.py`) and `RUNTIME_SUBPACKAGES` (`config`, `one`, `power_plant`, `runtimes`). Never `cdk/` or `agentcore_project/`.

The rule: **code that is copied imports, at module level, only the standard library, the `agentcore` dependency group, and other copied code.** Anything dev-only is imported inside the function that needs it:

- `json5` inside `Config.load_from_local_config_file` (runtimes read the config from SSM, `06`).
- `aws_cdk` and the stack modules inside the properties of `one/one_03_cdk.py`.

`test_assemble_runtime_dir` checks it: it imports the assembled runtimes and `one` in a subprocess where `aws_cdk`, `cdk_mate`, and `json5` raise `ImportError`.

To give a runtime a new dependency, add it to `[dependency-groups] agentcore` in `pyproject.toml` (and to the base dependencies too if the dev machine imports it), `uv lock`, then `mise run ac-gen`.

---

## 3. How the CLI installs the dependencies

At synth time (`agentcore build` or `deploy`), `@aws/agentcore-cdk` runs, for each runtime:

```text
uv pip install -r pyproject.toml --target <staging> --python-version 3.12
    --python-platform <platform> --only-binary :all:
```

for `aarch64-manylinux2014`, then `_2_28`, then `_2_34`, and keeps the first that works. **Wheels only, Linux aarch64.** A package version with no such wheel cannot be installed, and the CLI then reports only "uv install failed for all platform candidates".

`check_codezip_install()` runs the same command as a dry run and keeps uv's own message. `ac-deploy-<env>` runs it (`.mise/tasks/ac-check-wheels.py`) after `ac-gen`. Run it yourself after changing dependencies:

```bash
mise run ac-gen && .venv/bin/python .mise/tasks/ac-check-wheels.py
```

The fix for a version without wheels: constrain it out in `pyproject.toml` with a comment (an upper bound, or `!=<version>`), then `uv lock`. A release can reach PyPI before its wheels do: SQLAlchemy 2.1.7 was an sdist only for a while, which failed a deploy here, so this repo pins `sqlalchemy<2.1.0`. A package with no aarch64 wheel at all cannot be used in a CodeZip runtime; use a container build instead.

---

## 4. Size

A runtime zip is about 44 MB, almost all of it the `agentcore` group (strands, OpenTelemetry, boto3). The code copy is small. Keep the group to what the runtimes import; a smaller zip also starts faster (`02`, section 4.3).
