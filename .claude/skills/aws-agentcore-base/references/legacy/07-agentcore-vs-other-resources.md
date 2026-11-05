---
description: "The split between the AgentCore stack (deployed by the AgentCore CLI, TypeScript, only AgentCore wiring) and the agentcore_deps Python CDK stack (everything else the runtimes use), how agentcore.json refers to the latter by name, and where to give a runtime's execution role a new permission. Read before giving a runtime a permission, a database, a bucket, a secret, or a VPC, or before editing agentcore/cdk/."
---

# AgentCore and Everything Else

---

## 1. The rule

| What | Where | Deployed by |
| :--- | :--- | :--- |
| AgentCore resources: runtimes, their execution roles, endpoints, `bind()` between runtimes | `agentcore/agentcore.json` (generated) + `agentcore/cdk/lib/cdk-stack.ts` | `mise run ac-deploy-<env>` |
| Anything else the runtimes use: IAM policies, databases, buckets, secrets, VPCs | `<pkg>/cdk/stacks/agentcore_deps_stack.py`, the `agentcore_deps` entry of `StackCtxEnum` / `StackEnum` | `mise run cdk-up-<env>-agentcore-deps-stack` |

The AgentCore side only **refers** to the rest, by names from the config, through fields of `agentcore.json` that `ac-gen` fills in. No CloudFormation export or import is needed: every name and ARN is a deterministic config property.

So `cdk-stack.ts` stays the CLI's template plus the `bind()` lines, such as `runtime('PowerPlantMcp').bind(runtime('SiteAgent'))`, inside `if (this.application.runtimes.size > 0)` so an empty project (teardown) still synthesizes. `bind` must stay there: it needs the MCP runtime's ARN, which exists only inside the AgentCore stack.

---

## 2. Fields of `agentcore.json` that refer outward

Per runtime (schema of `@aws/agentcore-cdk`, `AgentEnvSpecSchema`):

| Field | Use | Used here |
| :--- | :--- | :--- |
| `additionalPolicies` | managed policy ARNs attached to the CLI-created execution role | yes: `config.iam_policy_arn_agentcore_runtime` |
| `envVars` | environment variables | yes (`06`) |
| `networkMode`, `networkConfig` | VPC mode, subnets, security groups (for a database in a VPC) | not yet |
| `executionRoleArn` | use an existing role instead of the CLI's | no (section 4) |

To add one, add it in `build_agentcore_json()` of `agentcore_project/project_files.py`, with its value from a config property, and assert it in `test_build_agentcore_json`.

---

## 3. Giving the runtimes a new permission

1. Add a `PolicyStatement` to `AgentCoreRuntimePolicy` in `agentcore_deps_stack.py`, with resource names or ARNs from the config.
2. Assert it in `tests/cdk/stacks/test_cdk_stacks_agentcore_deps_stack.py`.
3. `mise run cdk-up-<env>-agentcore-deps-stack` (the user's yes). No AgentCore deploy is needed: the policy is already attached.

If two runtimes need different permissions, add a second managed policy with its own names in `config_01_name.py`, and give each runtime its own `additionalPolicies` in `build_agentcore_json()`.

A new resource (a table, a bucket) goes in the same stack as a new `s0N_...` method; its name in the config; its permission in the policy; its name to the runtime through `envVars` only if the runtime cannot read it from the config.

---

## 4. Why `additionalPolicies`, not `executionRoleArn`

The CLI-created role already carries what every runtime needs (logs, X-Ray, Bedrock model access, workload identity), and `bind()` adds `bedrock-agentcore:InvokeAgentRuntime` to it. A role passed in with `executionRoleArn` is imported read-only: CDK drops the `bind()` grant with only a synth warning, and granting it from the Python stack would need the MCP runtime's ARN, which exists only after the AgentCore stack: a circular dependency.

---

## 5. Deploy order

The AgentCore stack refers to what `agentcore_deps` creates, so `agentcore_deps` goes first: `cdk-up-<env>-agentcore-deps-stack`, then `ac-deploy-<env>`; `ac-chain-up-<env>` runs them in that order, after the config. `ac-deploy-<env>` checks it (`one.check_agentcore_deps()`: the policy and the config parameter exist) and stops with the task to run if not. The chains are in `11`.
