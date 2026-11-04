---
description: "How runtime code knows where it runs (local, agentcore_local under agentcore dev, agentcore when deployed) and where its config and AWS session come from in each case: the config is one SSM SecureString, the env vars come from envVars in agentcore.json, and the boto session takes its region from AWS_REGION. Read when runtime code reads the config or calls AWS, when adding a config field a runtime uses, or when a runtime fails at startup."
---

# Runtime Detection and Config

The general rules (`runtime.py`, `Config.load`, `one.bsm`) are in the `pywf-aws-cdk-base` skill, references *Runtime*, *Boto Session*, and *Config Loading*. This file is what AgentCore adds.

---

## 1. Three places the same code runs

| Runtime | How it is started | Detected by | Config from | AWS credentials | Region |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `local` | `ac-local-*` tasks: the package from the repo | neither variable below | `config/*.json5` | profile `AWS_PROFILE_FOR_<ENV>` | the config's |
| `agentcore_local` | `ac-dev-*` tasks: `agentcore dev` runs the packaged copy in `app/<Runtime>/` | `IS_AGENTCORE_RUNTIME=true` and `LOCAL_DEV` set | SSM | profile `AWS_PROFILE_FOR_<ENV>` | `AWS_REGION` |
| `agentcore` | deployed | `IS_AGENTCORE_RUNTIME=true`, no `LOCAL_DEV` | SSM | the runtime's execution role | `AWS_REGION` |

- AgentCore documents no variable that says "you run on AgentCore", so the project sets `IS_AGENTCORE_RUNTIME=true` through `envVars` in `agentcore.json`.
- `agentcore dev` applies `envVars` too, and always sets `LOCAL_DEV=1` (plus `PORT`, and `FASTMCP_PORT` for an MCP runtime). `LOCAL_DEV` is undocumented CLI behavior (1.0.1): check it again after upgrading `@aws/agentcore`.
- The variable names are in `<pkg>/constants.py`. Never read them anywhere but `runtime.py`; ask `one.runtime.current_runtime_name()`.

---

## 2. The env vars every runtime gets

`ac-gen` writes them into `envVars` of every runtime in `agentcore.json`, for the environment it runs for (`project_files.get_runtime_env_vars`):

| Variable | Value |
| :--- | :--- |
| `IS_AGENTCORE_RUNTIME` | `true` |
| `ENV_NAME` | the environment, such as `dev` |
| `CONFIG_SSM_PARAM_NAME` | `config.ssm_param_name_config`, such as `/<project-slug>-dev/config` |

So both a deployed runtime and `agentcore dev` see the same three. `agentcore.json` is per environment because of this; it is git-ignored and regenerated (`03`).

---

## 3. The config is one SSM parameter

- `mise run config-deploy-<env>` writes the whole config of `<env>` as JSON to `config.ssm_param_name_config`, a `SecureString` with the AWS-managed key `aws/ssm`, only when it changed. `ac-deploy-<env>` runs it first.
- On `agentcore` and `agentcore_local`, `one.config` is `Config.load_from_ssm(ssm_client, os.environ["CONFIG_SSM_PARAM_NAME"])`. A missing parameter raises `ValueError` naming `config-deploy-<env>`.
- Why not env vars for the values: secrets (such as `db_connection_string`) would sit in plain text on the runtime, and the values would be spread over two places.
- Why not copy the config files into `app/`: they would be zipped into the CodeZip, secrets included.
- Reading it costs one `GetParameter` per process, cached in `one.config`: one per runtime session (`02`). That is far below the SSM throughput limit, unlike a Lambda function under high concurrency.
- The execution role reads it through the `agentcore_deps` policy (`07`). No `kms:Decrypt` grant is needed: the `aws/ssm` key policy allows its use through SSM in the account.

---

## 4. The boto session on a runtime

On `agentcore` and `agentcore_local`, `one.bsm` takes its region from `AWS_REGION`, not from the config, because the config is read through that session (using the config would recurse). It is passed explicitly: botocore reads only `AWS_DEFAULT_REGION`. AgentCore sets `AWS_REGION`; the `ac-dev-*` tasks set it for `agentcore dev`.

Libraries that build their own boto3 session (such as `BedrockModel` in Strands) follow the standard chain: the execution role when deployed, `AWS_PROFILE` locally (the `ac-*-agent` tasks set it).

---

## 5. Fail at startup

Each runtime's `main()` loads `one.config` (and `one.engine` for the MCP server) and prints where it came from, with `flush=True`, before serving:

```text
Loaded the config of 'dev' on runtime 'agentcore'
Connected to the database sqlite+pysqlite:///%3Amemory%3A
```

A runtime that cannot read its config fails before taking traffic, and the log says why. Under `agentcore dev`, an HTTP runtime is served by uvicorn without `main()`, so its config loads on the first request.
