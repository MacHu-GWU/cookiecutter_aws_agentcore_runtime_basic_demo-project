---
name: aws-agentcore-debug
description: "Find out why a runtime of this AgentCore project fails, is slow, or answers wrongly, locally, under agentcore dev, or deployed in an environment: pin down where and which runtime, read the output and the logs (read only), match the symptom to the failures met so far, and name the cause with evidence before any fix. Use when the user reports an error, a 4xx or 5xx, a timeout, a slow agent, a runtime that does not start, a deploy that fails, or an answer that is wrong."
argument-hint: "[local|dev-server|env] [runtime] [symptom]"
---

Find the cause of one problem with one runtime, by reading before changing anything. The fix itself goes to the skill that owns the change.

## 0. Know where, which, and what

Three things, each from the user's words, the arguments (`$ARGUMENTS`), or an error the user pasted:

| What | Choices | From |
| :--- | :--- | :--- |
| **Where** it fails | `local` (`ac-local-<slug>`, tests), `agentcore_local` (`ac-dev-<slug>`), or deployed in an environment | the four runtimes of `10`, section 1; the environments of `EnvNameEnum` in `<package_name>/env.py` |
| **Which** runtime | the runtimes of the registry, `get_runtime_specs(config)` in `<package_name>/agentcore_project/registry.py` | match its name, slug, or module |
| **What** happens | the error text, the status code, the slow step, the wrong answer | the user, or the output of re-running the failing task |

Ask only for what is still missing, offering the real choices from the registry and `EnvNameEnum`; never guess an environment. If the project has one runtime of the kind the user describes, use it and say so.

## 1. Read

Read ../aws-agentcore-base/SKILL.md, then:
- ../aws-agentcore-base/references/80-invoke-and-observe.md

And by where it fails:
- local: ../aws-agentcore-base/references/30-mcp-runtime.md or ../aws-agentcore-base/references/40-agent-runtime.md
- `agentcore_local`: ../aws-agentcore-base/references/53-agentcore-dev.md
- deployed, or the deploy itself fails: ../aws-agentcore-base/references/60-deploy.md

And by symptom: ../aws-agentcore-base/references/10-code-runtime.md when the runtime is detected wrongly, ../aws-agentcore-base/references/20-centralized-config.md when the config does not load, ../aws-agentcore-base/references/52-agentcore-packaging.md for an import error or a failed install, ../aws-agentcore-base/references/90-maintain.md (section 2) when the CLI behaves differently than the references say. A short citation such as `80` means the reference of that number.

## 2. Look, without changing anything

Everything here is read only; none of it needs the user's yes, except that calling an agent calls its model (say so first).

| Where | Look at |
| :--- | :--- |
| local | re-run the failing task or test and read its whole output; the config source line `main()` prints |
| `agentcore_local` | the same, plus whether the config is deployed (`config-deploy-<env>` has run) and the port is the registry's |
| deployed | `mise run ac-status-<env>`; `mise run ac-logs-<env>-<slug>` (`SINCE=2h` for longer); `QUICK_LINKS.md` for the console pages; `mise run ac-invoke-<env>-<slug>` to reproduce, with `SESSION_ID` to stay in one session |

Then match the symptom: `80`, section 6 for an invocation, `60`, section 7 for a deploy. For slowness, the time breakdown of `80`, section 3: send the same prompt three times with one session ID, and read where the gap is (a cold microVM, the first MCP response, the model).

## 3. Name the cause

State the cause and the evidence for it (the log line, the output, the table row), and the fix, before changing anything. Then hand it over:

| The fix is in | Use |
| :--- | :--- |
| an MCP runtime's code, tools, dependency, or permission | `aws-agentcore-change-mcp` |
| an agent's prompt, tools, model, MCP connections, or contract | `aws-agentcore-change-agent` |
| something deployed lagging behind the code (config, stack, runtimes) | `aws-agentcore-deploy` |
| the CLI or the toolchain behaving differently | `90`, sections 1 and 2 |

A one-line fix that is obviously right (a typo, a missing `.env` entry the user owns) can be made here after the user's yes.

## 4. Report

The where, which, and what of section 0, the cause with its evidence, the fix and which skill makes it, and what was not checked. A failure the tables of `80`, section 6 or `60`, section 7 do not list yet: propose the row to add, and add it to that table when the user agrees.
