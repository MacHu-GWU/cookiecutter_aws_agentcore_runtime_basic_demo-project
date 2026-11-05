---
name: aws-agentcore-deploy
description: "Deploy this AgentCore project's changes to one environment, with the user's yes: work out which steps of the deploy chain the change needs (config, the agentcore_deps stack, the runtimes), check the change locally first, run the steps through mise, then test the deployed runtimes and do the follow-ups (deployed-state.json, QUICK_LINKS.md). Use when the user wants to deploy, ship, release to, or update an environment such as dev, tst, or prd, or asks whether a change is live."
argument-hint: "[env]"
---

Put a change into one environment through the generated mise tasks, choosing the steps, asking before each environment, and proving it works there. The tasks do the work; this skill decides which ones, in what order, and what to check.

## 0. Know which environment

The environments are the members of `EnvNameEnum` in `<package_name>/env.py`. Match the user's words and the arguments (`$ARGUMENTS`) against them.

- **One named**: say "Deploying to `<env>`" in the first line and go on.
- **None named**: ask which one, offering the members of `EnvNameEnum`. The default of `ENV_NAME` (`dev`) is not an answer: deploying changes AWS, so the user names the environment.
- **Several**, or "everywhere": one environment at a time, in the order `EnvNameEnum` lists them, each with its own yes, and the next only after the previous one is tested.
- **Not this skill's job**: taking an environment down is `mise run ac-chain-down-<env>` (`70`); a deploy that fails for an unknown reason is `aws-agentcore-debug`.

## 1. Read

Read ../aws-agentcore-base/SKILL.md, then:
- ../aws-agentcore-base/references/60-deploy.md

Read ../aws-agentcore-base/references/20-centralized-config.md when the config changed, ../aws-agentcore-base/references/80-invoke-and-observe.md for the tests after the deploy, and ../aws-agentcore-base/references/70-teardown.md only if the user wants something removed. A short citation such as `60` means the reference of that number.

## 2. Work out the steps

The chain is fixed (`60`, section 2): `config-deploy-<env>`, then `cdk-up-<env>-agentcore-deps-stack`, then `ac-deploy-<env>`. Map what changed to the steps it needs, from what the user says and from the diff (uncommitted changes, and commits since the last change to `agentcore/.cli/deployed-state.json`, which is only a hint):

| What changed | Steps |
| :--- | :--- |
| `config/*.json5` or the config model | `config-deploy-<env>` (a new session reads it); plus `ac-deploy-<env>` if a runtime's code changed with it |
| `agentcore_deps_stack.py`, or the names it uses | `cdk-up-<env>-agentcore-deps-stack` |
| runtime code, the registry, `cdk-stack.ts`, the `agentcore` dependency group | `ac-deploy-<env>` |
| several of these, the first deploy to the environment, or not sure | the whole chain: `ac-chain-up-<env>` |

Steps run in the chain's order, never skipped backwards: a new permission goes out before the code that needs it.

## 3. Check before asking

Run, and stop at the first failure (fixing it is the change's own skill, not this one):

```bash
mise run format && mise run lint
mise run cov
mise run ac-check-wheels
mise run ac-build
```

For a stack change, also `mise run cdk-plan-<env>-agentcore-deps-stack`: it changes nothing, and its diff goes into the plan below.

Then show the plan in one message and wait for the user's yes: the environment, the profile it uses (`AWS_PROFILE_FOR_<ENV>`, not its value), the steps and why each, and what the stack diff shows. For `prd`, say so plainly in the question.

## 4. Deploy

Run the steps through mise, in the background when they may take more than two minutes, and read their output:

```bash
mise run ac-chain-up-<env>
```

or the single steps of section 2. At the first failure, stop: look the message up in `60`, section 7; if it is not there, switch to `aws-agentcore-debug`. Never retry a different step order or a raw `agentcore` / `cdk` command to get past a failure.

## 5. Test it there

1. `mise run ac-test-<env>`: the status, then every runtime invoked once with its sample payload (`60`, section 4). An agent calls its model: say so first.
2. If the change was about a specific tool or prompt the samples do not reach, `ac-invoke-<env>-<slug>` with that payload, or the client of `80`, section 1.
3. A deploy reaches new sessions only (`60`, section 3): a test with an old session ID still sees the old code.
4. `mise run int-test` if the user wants the integration tests (`80`, section 5): it calls the deployed runtimes and the model.

## 6. Follow-ups

- `agentcore/.cli/deployed-state.json` changed: it must be committed (`60`, section 5). Say so and offer to commit it; commit only on the user's yes.
- A runtime was created or replaced: `mise run gen-quick-links` (reads AWS), and `QUICK_LINKS.md` is committed with it.

## 7. Report

The environment, the steps run, each one's result, the answers of the deployed runtimes, the follow-ups done and not done, and anything not verified. A deploy failure that `60`, section 7 did not list: propose a row for that table.
