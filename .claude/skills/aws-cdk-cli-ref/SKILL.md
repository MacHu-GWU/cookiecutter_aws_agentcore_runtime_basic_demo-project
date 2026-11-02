---
name: aws-cdk-cli-ref
description: Index of the official AWS CDK CLI reference as Markdown pages on docs.aws.amazon.com, one URL per cdk command (deploy, diff, synth, destroy, bootstrap, list, rollback, drift, watch, import, refactor, gc, ...) and per CLI topic (cdk.json and options, credentials, bootstrapping, troubleshooting). Use when you need what a cdk CLI command or option does, its arguments and defaults, or how the CLI behaves, so you fetch the one relevant page instead of guessing.
---

# AWS CDK CLI reference index

AWS publishes every CDK Developer Guide page as Markdown: the `.html` URL with `.md` instead. This skill only maps a question to the right page. **Fetch the page** (WebFetch, or `curl -sL <url>`), then answer from it; do not answer option details from memory.

## How to use

1. Find the command or topic below, and fetch its `.md` URL.
2. The docs describe the **latest** CLI. For the CLI actually installed, check `cdk --version` and `cdk <command> --help`. When they disagree, the installed CLI wins.
3. Not listed here: search the official index, https://docs.aws.amazon.com/cdk/v2/guide/llms.txt, which lists every page of the guide with a one-line summary.

All URLs share the prefix `https://docs.aws.amazon.com/cdk/v2/guide/`.

## Commands

| Command | Page | What it covers |
| :--- | :--- | :--- |
| `cdk acknowledge` (`ack`) | `ref-cli-cmd-ack.md` | hide a notice by its ID |
| `cdk bootstrap` | `ref-cli-cmd-bootstrap.md` | deploy the CDKToolkit stack into an environment |
| `cdk context` | `ref-cli-cmd-context.md` | list and clear cached context values |
| `cdk deploy` | `ref-cli-cmd-deploy.md` | deploy stacks; approval, hotswap, change sets, parameters |
| `cdk destroy` | `ref-cli-cmd-destroy.md` | delete stacks |
| `cdk diff` | `ref-cli-cmd-diff.md` | compare local stacks with deployed ones |
| `cdk docs` | `ref-cli-cmd-docs.md` | open the docs in a browser |
| `cdk doctor` | `ref-cli-cmd-doctor.md` | inspect the local project and environment |
| `cdk drift` | `ref-cli-cmd-drift.md` | detect drift of deployed stacks |
| `cdk flags` | `ref-cli-cmd-flags.md` | view and change feature flags |
| `cdk gc` | `ref-cli-cmd-gc.md` | garbage-collect unused bootstrap assets |
| `cdk import` | `ref-cli-cmd-import.md` | import existing resources into a stack |
| `cdk init` | `ref-cli-cmd-init.md` | create a project from a template |
| `cdk list` (`ls`) | `ref-cli-cmd-list.md` | list stacks and dependencies |
| `cdk metadata` | `ref-cli-cmd-metadata.md` | show a stack's metadata |
| `cdk migrate` | `ref-cli-cdk-migrate.md` | turn deployed resources or templates into a CDK app (note the irregular page name) |
| `cdk notices` | `ref-cli-cmd-notices.md` | show notices |
| `cdk orphan` | `ref-cli-cmd-orphan.md` | detach resources from a stack without deleting them |
| `cdk publish-assets` | `ref-cli-cmd-publish-assets.md` | publish assets without deploying |
| `cdk refactor` | `ref-cli-cmd-refactor.md` | move or rename resources without replacing them |
| `cdk rollback` | `ref-cli-cmd-rollback.md` | roll a failed or paused stack back to a stable state |
| `cdk synth` (`synthesize`) | `ref-cli-cmd-synth.md` | synthesize the cloud assembly and templates |
| `cdk watch` | `ref-cli-cmd-watch.md` | watch files and deploy or hotswap on change |
| all commands, global options | `ref-cli-cmd.md` | the command list and the options every command accepts |

No reference page (CLI 2.1145.0): `cdk validate`, `cdk diagnose`, `cdk lsp`, `cdk cli-telemetry` (for telemetry, see `cli-telemetry.md` below). Use `cdk <command> --help`.

## CLI topics

| Topic | Page |
| :--- | :--- |
| CLI overview: how options and booleans (`--no-<option>`) are written, authentication, region, the app command, specifying stacks, context values, `cdk.json` configuration | `cli.md` |
| Credentials and profiles the CLI uses | `configure-access.md` |
| Environments (account and region) of stacks | `configure-env.md` |
| Bootstrapping, and customizing it | `bootstrapping-env.md`, `bootstrapping-customizing.md` |
| Context values from the CLI or `cdk.json` | `get-context-var.md` |
| Deployment problems | `deploy-troubleshoot.md` |
| General troubleshooting | `troubleshooting.md` |
| CLI telemetry | `cli-telemetry.md` |
| CLI and library versioning; supported Node.js versions | `versioning.md`, `node-versions.md` |
| The whole guide in one file (large) | `full.md` |

## The installed CLI's own option list

The `aws-cdk` npm package ships `lib/cli/cli-type-registry.json`: every command and option of that exact version, with type, description, default, and choices. Find it from the executable: `<prefix>/bin/cdk` resolves to `<prefix>/lib/node_modules/aws-cdk/bin/cdk`, so the file is `<prefix>/lib/node_modules/aws-cdk/lib/cli/cli-type-registry.json`. Prefer it to the web docs when the question is "does my installed CLI support option X".
