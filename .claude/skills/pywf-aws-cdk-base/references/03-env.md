---
description: "The environment: which deployment environment (dev, tst, prd) the code targets, how ENV_NAME selects the current one, and the rule that everything environment specific belongs to the current environment. Read when code depends on the environment, when switching environments, or when adding one."
---

# Environment

Seed repo: [`env.py`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/cookiecutter_aws_cdk_demo/env.py).

---

## 1. What it is

The environment is **which** deployment the code targets, independent of where it runs (`02-runtime.md`). `EnvNameEnum` lists every environment: `dev`, `tst`, `prd`. Each one usually lives in its own AWS account.

---

## 2. The current environment

- The `ENV_NAME` environment variable selects it; unset means `dev`. A value outside `EnvNameEnum` raises `ValueError`.
- Locally, `.env` may set it; a task or command that targets one environment sets it for its own process, as in `ENV_NAME=prd mise run int-test`.
- `one.env.current_env_name` (a string such as `"dev"`) is computed once and cached for the life of the process.

---

## 3. One process, one environment

Everything environment specific (the config, the boto session, and whatever is built from them) belongs to the current environment. Code never loops over environments inside one process to act on each; to act on another environment, start a new process with another `ENV_NAME`. The only exception is a tool that needs every environment at once without calling AWS, such as one that prints a URL per environment: it builds a fresh `One()` per environment and sets its `config` explicitly.

---

## 4. Adding an environment

1. Add a member to `EnvNameEnum`.
2. Add `config/config-<env>.json5`, and a `config/config-<env>-secret.json5` for your machine; `config/example/` shows the shape of each.
3. Add `AWS_PROFILE_FOR_<ENV>` to `.env.example` and your `.env`.
4. Then follow the specific files for what else the new environment needs.
