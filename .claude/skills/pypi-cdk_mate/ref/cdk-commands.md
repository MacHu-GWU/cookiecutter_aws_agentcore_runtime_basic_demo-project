# cdk_mate 1.0.0: CDK Command Classes

Every class is `cdk_mate.cli.<Name>` (from `import cdk_mate.api as cdk_mate`), a dataclass subclass of `cdk_mate.cli.BaseCommand`, generated from aws-cdk CLI 2.1145.0. Each has `.to_args() -> list[str]` and `.run(bsm=None, dir_cdk=None)`; see `public-api.md` for those and for the global fields (`profile`, `region`, `context`, `app`, `output`, `verbose`, `cdk_cmd`, `extra_args`, ...) that every class also accepts.

Every field defaults to "not set" (omitted from the command line). Value rules: `bool` → `--x` / `--no-x`; `list` → option repeated (positional lists are space-separated after the subcommand); `dict` → `KEY=VALUE`; `int` `0` is passed; `None` / `""` pass nothing. A trailing `_` in a field name is dropped (`list_` → `--list`). "(positional)" fields come right after the subcommand.

Official option docs for each command: `https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-<command>.html`.

## `Acknowledge`: `cdk acknowledge`

Acknowledge a notice so that it does not show up anymore.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `notice_id` (positional) | `str` | The `ID` positional argument. |

## `Bootstrap`: `cdk bootstrap`

Deploys the CDK toolkit stack into an AWS environment.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `aws_environment` (positional) | `list[str]` | The `ENVIRONMENTS` positional argument. |
| `bootstrap_bucket_name` | `str` | The name of the CDK toolkit bucket; bucket will be created and must not exist. |
| `bootstrap_customer_key` | `bool` | Create a Customer Master Key (CMK) for the bootstrap bucket (you will be charged but can customize permissions, modern bootstrapping only). |
| `bootstrap_kms_key_id` | `str` | AWS KMS master key ID used for the SSE-KMS encryption (specify AWS_MANAGED_KEY to use an AWS-managed key). |
| `cloudformation_execution_policies` | `list[str]` | The Managed Policy ARNs that should be attached to the role performing deployments into this environment (may be repeated, modern bootstr... |
| `custom_permissions_boundary` | `str` | Use the permissions boundary specified by name. |
| `deny_external_id` | `bool` | Block AssumeRole access to all boostrapped roles if an ExternalId is provided (enabled by default). |
| `example_permissions_boundary` | `bool` | Use the example permissions boundary. |
| `execute` | `bool` | Whether to execute the change set (--no-execute will NOT execute the change set) (default true). |
| `express` | `bool` | Whether creation of bootstrap stack should use CloudFormation Express mode (default false). |
| `force` | `bool` | Always bootstrap even if it would downgrade template version (default false). |
| `import_existing_resources` | `bool` | Whether to import existing resources into the bootstrap stack instead of failing if they already exist (default true). |
| `previous_parameters` | `bool` | Use previous values for existing parameters (you must specify all parameters on every deployment if this is disabled) (default true). |
| `public_access_block_configuration` | `bool` | Block public access configuration on CDK toolkit bucket (enabled by default). |
| `qualifier` | `str` | String which must be unique for each bootstrap stack. You must configure it on your CDK app if you change this from the default. |
| `show_template` | `bool` | Instead of actual bootstrapping, print the current CLI's bootstrapping template to stdout for customization (default false). |
| `tags` | `dict[str, str]` | Tags to add for the stack (KEY=VALUE). |
| `template` | `str` | Use the template from the given file instead of the built-in one (use --show-template to obtain an example). |
| `termination_protection` | `bool` | Toggle CloudFormation termination protection on the bootstrap stacks. |
| `toolkit_stack_name` | `str` | The name of the CDK toolkit stack to create. |
| `trust` | `list[str]` | The AWS account IDs that should be trusted to perform deployments into this environment (may be repeated, modern bootstrapping only). |
| `trust_for_lookup` | `list[str]` | The AWS account IDs that should be trusted to look up values in this environment (may be repeated, modern bootstrapping only). |
| `untrust` | `list[str]` | The AWS account IDs that should not be trusted by this environment (may be repeated, modern bootstrapping only). |

## `CliTelemetry`: `cdk cli-telemetry`

Enable or disable anonymous telemetry.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `disable` | `bool` | Disable anonymous telemetry. |
| `enable` | `bool` | Enable anonymous telemetry. |
| `status` | `bool` | Report telemetry opt-in/out status. |

## `Context`: `cdk context`

Manage cached context values.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `clear` | `bool` | Clear all context (default false). |
| `force` | `bool` | Ignore missing key error (default false). |
| `reset` | `str` | The context key (or its index) to reset. |

## `Deploy`: `cdk deploy`

Deploys the stack(s) named STACKS into your AWS account.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `list[str]` | The `STACKS` positional argument. |
| `all` | `bool` | Deploy all available stacks (default false). |
| `asset_build_concurrency` | `int` | Maximum number of asset builds to run in parallel (default 1). |
| `asset_parallelism` | `bool` | Whether to build/publish assets in parallel. |
| `asset_prebuild` | `bool` | Whether to build all assets before deploying the first stack (useful for failing Docker builds) (default true). |
| `build_exclude` | `list[str]` | Do not rebuild asset with the given ID. Can be specified multiple times. |
| `change_set_name` | `str` | Name of the CloudFormation change set to create (only if method is not direct). |
| `concurrency` | `int` | Maximum number of simultaneous deployments (dependency permitting) to execute (default 1). |
| `exclusively` | `bool` | Only deploy requested stacks, don't include dependencies. |
| `execute` | `bool` | Deprecated. Whether to execute the change set (--no-execute will NOT execute the change set) (deprecated). |
| `express` | `bool` | Perform the CloudFormation deployment using Express Mode, a faster mode of deployment which skips stabilization and has automatic rollbac... |
| `force` | `bool` | Always deploy stack even if templates are identical (default false). |
| `hotswap` | `bool` | Attempts to perform a 'hotswap' deployment, but does not fall back to a full deployment if that is not possible. Instead, changes to any... |
| `hotswap_ecs_maximum_healthy_percent` | `int` | Upper limit on the number of your service's tasks that are allowed in the RUNNING or PENDING state during a deployment, as a percentage o... |
| `hotswap_ecs_minimum_healthy_percent` | `int` | Lower limit on the number of your service's tasks that must remain in the RUNNING state during a deployment, as a percentage of the desir... |
| `hotswap_ecs_stabilization_timeout_seconds` | `int` | Number of seconds to wait for a single service to reach stable state, where the desiredCount is equal to the runningCount. |
| `hotswap_fallback` | `bool` | Attempts to perform a 'hotswap' deployment, which skips CloudFormation and updates the resources directly, and falls back to a full deplo... |
| `ignore_no_stacks` | `bool` | Whether to deploy if the app contains no stacks (default false). |
| `import_existing_resources` | `bool` | Indicates if the stack set imports resources that already exist (default false). |
| `logs` | `bool` | Show CloudWatch log events from all resources in the selected Stacks in the terminal. 'true' by default, use --no-logs to turn off. Only... |
| `method` | `T.Literal["direct", "change-set", "prepare-change-set", "execute-change-set"]` | How to perform the deployment. "change-set" (default) creates and executes a change set. "prepare-change-set" creates a change set withou... |
| `notification_arns` | `list[str]` | ARNs of SNS topics that CloudFormation will notify with stack related events. These will be added to ARNs specified with the 'notificatio... |
| `outputs_file` | `str` | Path to file where stack outputs will be written as JSON. |
| `parameters` | `dict[str, str]` | Additional parameters passed to CloudFormation at deploy time (STACK:KEY=VALUE). |
| `previous_parameters` | `bool` | Use previous values for existing parameters (you must specify all parameters on every deployment if this is disabled) (default true). |
| `progress` | `T.Literal["bar", "events", "errors-only"]` | Display mode for stack activity events. |
| `require_approval` | `T.Literal["never", "any-change", "broadening", "destructive"]` | What changes require manual approval. |
| `revert_drift` | `bool` | Create a drift-aware change set that brings actual resource states in line with template definitions (default false). |
| `rollback` | `bool` | Rollback stack to stable state on failure. Defaults to 'true' for non-express mode deployments, defaults to 'false' for express mode depl... |
| `tags` | `dict[str, str]` | Tags to add to the stack (KEY=VALUE), overrides tags from Cloud Assembly (deprecated). |
| `toolkit_stack_name` | `str` | The name of the existing CDK toolkit stack (only used for app using legacy synthesis). |
| `watch` | `bool` | Continuously observe the project files, and deploy the given stack(s) automatically when changes are detected. Implies --hotswap by default. |

## `Destroy`: `cdk destroy`

Destroy the stack(s) named STACKS.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `list[str]` | The `STACKS` positional argument. |
| `all` | `bool` | Destroy all available stacks (default false). |
| `concurrency` | `int` | Maximum number of simultaneous destroys (dependency permitting) to execute (default 1). |
| `exclusively` | `bool` | Only destroy requested stacks, don't include dependees. |
| `express` | `bool` | Destroy stack(s) using Express Mode, a faster mode of tearing down stacks which skips stabilization and has automatic rollback disabled b... |
| `force` | `bool` | Do not ask for confirmation before destroying the stacks. |

## `Diagnose`: `cdk diagnose`

Find the root cause(s) of stack deployment failures.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `list[str]` | The `STACKS` positional argument. |
| `concurrency` | `int` | How many stacks to diagnose in parallel. |
| `toolkit_stack_name` | `str` | The name of the existing CDK toolkit stack (only used for app using legacy synthesis). |

## `Diff`: `cdk diff`

Compares the specified stack with the deployed stack or a local template file, and returns with status 1 if any difference is found.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `list[str]` | The `STACKS` positional argument. |
| `change_set` | `bool` | Deprecated, use --method instead. Whether to create a change set to analyze resource replacements. In this mode, diff will use the deploy... |
| `change_set_name` | `str` | Name of the CloudFormation change set to create (only if method is not template). |
| `context_lines` | `int` | Number of context lines to include in arbitrary JSON diff rendering (default 3). |
| `exclusively` | `bool` | Only diff requested stacks, don't include dependencies. |
| `fail` | `bool` | Fail with exit code 1 in case of diff. Same as --fail-on=any-change. |
| `fail_on` | `T.Literal["never", "any-change", "broadening", "destructive"]` | Fail with exit code 1 when the diff contains the given kind of change. "any-change" fails on any difference, "broadening" only on changes... |
| `import_existing_resources` | `bool` | Whether or not the change set imports resources that already exist (default false). |
| `include_moves` | `bool` | Whether to include moves in the diff (default false). |
| `method` | `T.Literal["auto", "change-set", "template"]` | How to compute the diff. "auto" attempts to create a change set and falls back to template-only on failure. "change-set" creates a change... |
| `processed` | `bool` | Whether to compare against the template with Transforms already processed (default false). |
| `quiet` | `bool` | Do not print stack name and default message when there is no diff to stdout (default false). |
| `security_only` | `bool` | Only diff for broadened security changes (default false). |
| `template` | `str` | The path to the CloudFormation template to compare with. Implies --method=template. |

## `Doctor`: `cdk doctor`

Check your set-up for potential problems.

No own fields; global fields only.

## `Drift`: `cdk drift`

Detect drifts in the given CloudFormation stack(s).

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `list[str]` | The `STACKS` positional argument. |
| `fail` | `bool` | Fail with exit code 1 if drift is detected. |

## `Flags`: `cdk flags`

View and toggle feature flags.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `flag_names` (positional) | `list[str]` | The `FLAGNAME` positional argument. |
| `all` | `bool` | Modify or view all feature flags. |
| `concurrency` | `int` | Maximum number of simultaneous synths to execute (default 4). |
| `default` | `bool` | Change flags to default state. |
| `interactive` | `bool` | Interactive option for the flags command. |
| `recommended` | `bool` | Change flags to recommended states. |
| `safe` | `bool` | Enable all feature flags that do not impact the user's application. |
| `set` | `bool` | Signifies the user would like to modify their feature flag configuration. |
| `unconfigured` | `bool` | Modify unconfigured feature flags. |
| `value` | `str` | The value the user would like to set the feature flag configuration to. |

## `GC`: `cdk gc`

Garbage collect assets. Options detailed here: https://github.com/aws/aws-cdk-cli/tree/main/packages/aws-cdk#cdk-gc.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `aws_environment` (positional) | `list[str]` | The `ENVIRONMENTS` positional argument. |
| `action` | `str` | The action (or sub-action) you want to perform. Valid entires are "print", "tag", "delete-tagged", "full" (default "full"). |
| `bootstrap_stack_name` | `str` | Deprecated, use --toolkit-stack-name. The name of the CDK toolkit stack, if different from the default "CDKToolkit" (deprecated, use --to... |
| `confirm` | `bool` | Confirm via manual prompt before deletion (default true). |
| `created_buffer_days` | `int` | Never delete assets younger than this (in days) (default 1). |
| `rollback_buffer_days` | `int` | Delete assets that have been marked as isolated for this many days (default 0). |
| `toolkit_stack_name` | `str` | The name of the CDK toolkit stack, if different from the default "CDKToolkit". |
| `type` | `str` | Specify either ecr, s3, or all (default "all"). |

## `Import`: `cdk import`

Import existing resource(s) into the given STACK.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `str` | The `STACK` positional argument. |
| `change_set_name` | `str` | Name of the CloudFormation change set to create. |
| `execute` | `bool` | Whether to execute the change set (--no-execute will NOT execute the change set) (default true). |
| `force` | `bool` | Do not abort if the template diff includes updates or deletes. This is probably safe but we're not sure, let us know how it goes. |
| `notification_arns` | `list[str]` | ARNs of SNS topics that CloudFormation will notify with stack related events. These will be added to ARNs specified with the 'notificatio... |
| `record_resource_mapping` | `str` | If specified, CDK will generate a mapping of existing physical resources to CDK resources to be imported as. The mapping will be written... |
| `resource_mapping` | `str` | If specified, CDK will use the given file to map physical resources to CDK resources for import, instead of interactively asking the user... |
| `resource_mapping_inline` | `str` | Inline JSON resource mapping, e.g. '{"MyResource":{"TableName":"my-table"}}'. |
| `rollback` | `bool` | Rollback stack to stable state on failure. Defaults to 'true', iterate more rapidly with --no-rollback or -R. Note: do \*\*not\*\* disabl... |
| `toolkit_stack_name` | `str` | The name of the CDK toolkit stack to create. |

## `Init`: `cdk init`

Create a new, empty CDK project from a template.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `template_type` (positional) | `str` | The `TEMPLATE` positional argument. |
| `from_path` | `str` | Path to a local custom template directory or multi-template repository. |
| `generate_only` | `bool` | If true, only generates project files, without executing additional operations such as setting up a git repo, installing dependencies or... |
| `language` | `T.Literal["csharp", "cs", "fsharp", "fs", "go", "java", "javascript", "js", "python", "py", "typescript", "ts"]` | The language to be used for the new project (default can be configured in ~/.cdk.json). |
| `lib_version` | `str` | The version of the CDK library (aws-cdk-lib) to initialize built-in templates with. Defaults to the version that was current when this CL... |
| `list_` | `bool` | List the available templates. |
| `package_manager` | `T.Literal["npm", "yarn", "pnpm", "bun"]` | The package manager to use to install dependencies. Only applicable for TypeScript and JavaScript projects. Defaults to npm in TypeScript... |
| `project_name` | `str` | The name of the new project. |
| `template_path` | `str` | Path to a specific template within a multi-template repository. |

## `List`: `cdk list`

Lists all stacks in the app.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `list[str]` | The `STACKS` positional argument. |
| `long` | `bool` | Display environment information for each stack (default false). |
| `show_dependencies` | `bool` | Display stack dependency information for each stack (default false). |

## `Metadata`: `cdk metadata`

Returns all metadata associated with this stack.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stack` (positional) | `str` | The `STACK` positional argument. |

## `Migrate`: `cdk migrate`

Migrate existing AWS resources into a CDK app.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `account` | `str` | The account to retrieve the CloudFormation stack template from. |
| `compress` | `bool` | Use this flag to zip the generated CDK app. |
| `filter` | `list[str]` | Filters the resource scan based on the provided criteria in the following format: "key1=value1,key2=value2" This field can be passed mult... |
| `from_path` | `str` | The path to the CloudFormation template to migrate. Use this for locally stored templates. |
| `from_scan` | `str` | Determines if a new scan should be created, or the last successful existing scan should be used options are "new" or "most-recent". |
| `from_stack` | `bool` | Use this flag to retrieve the template for an existing CloudFormation stack. |
| `language` | `T.Literal["typescript", "ts", "go", "java", "python", "py", "csharp", "cs"]` | The language to be used for the new project (default "typescript"). |
| `output_path` | `str` | The output path for the migrated CDK app. |
| `stack_name` | `str` | The name assigned to the stack created in the new project. The name of the app will be based off this name as well. |

## `Notices`: `cdk notices`

Returns a list of relevant notices.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `unacknowledged` | `bool` | Returns a list of unacknowledged notices (default false). |

## `Orphan`: `cdk orphan`

Detach resources from a CloudFormation stack without deleting them.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `paths` (positional) | `list[str]` | The `PATHS` positional argument. |

## `PublishAssets`: `cdk publish-assets`

Publish assets for the given stack(s) without deploying.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `list[str]` | The `STACKS` positional argument. |
| `all` | `bool` | Publish assets for all available stacks (default false). |
| `concurrency` | `int` | Maximum number of simultaneous asset operations (building and publishing, dependency permitting) to execute (default 4). |
| `exclusively` | `bool` | Only publish assets for requested stacks, don't include dependencies. |
| `force` | `bool` | Always publish assets, even if they are already published (default false). |

## `Refactor`: `cdk refactor`

Moves resources between stacks or within the same stack.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `list[str]` | The `STACKS` positional argument. |
| `additional_stack_name` | `list[str]` | Names of deployed stacks to be considered for resource comparison. |
| `dry_run` | `bool` | Do not perform any changes, just show what would be done (default false). |
| `force` | `bool` | Whether to do the refactor without asking for confirmation (default false). |
| `override_file` | `str` | A file that declares overrides to be applied to the list of mappings computed by the CLI. |
| `revert` | `bool` | If specified, the command will revert the refactor operation. This is only valid if a mapping file was provided (default false). |
| `toolkit_stack_name` | `str` | The name of the existing CDK toolkit stack (used to find the staging bucket for templates that are too large to be sent inline). |

## `Rollback`: `cdk rollback`

Rolls back the stack(s) named STACKS to their last stable state.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `list[str]` | The `STACKS` positional argument. |
| `all` | `bool` | Roll back all available stacks (default false). |
| `force` | `bool` | Orphan all resources for which the rollback operation fails. |
| `orphan` | `list[str]` | Orphan the given resources, identified by their logical ID (can be specified multiple times). |
| `toolkit_stack_name` | `str` | The name of the CDK toolkit stack the environment is bootstrapped with. |
| `validate_bootstrap_version` | `bool` | Whether to validate the bootstrap stack version. Defaults to 'true', disable with --no-validate-bootstrap-version. |

## `Synth`: `cdk synth`

Synthesizes and prints the CloudFormation template for this stack.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `list[str]` | The `STACKS` positional argument. |
| `exclusively` | `bool` | Only synthesize requested stacks, don't include dependencies. |
| `quiet` | `bool` | Do not output CloudFormation Template to stdout (default false). |
| `validation` | `bool` | After synthesis, validate stacks with the "validateOnSynth" attribute set (can also be controlled with CDK_VALIDATION) (default true). |
| `watch` | `bool` | Continuously observe the project files, and synthesize the given stack(s) automatically when changes are detected. Never deploys, and nev... |

## `Validate`: `cdk validate`

Validate synthesized CloudFormation templates against policy rules.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `list[str]` | The `STACKS` positional argument. |
| `online` | `bool` | Submit templates to CloudFormation for early validation (requires AWS credentials) (default true). |
| `watch` | `bool` | Continuously observe the project files, and validate the given stack(s) automatically when changes are detected. Never deploys. Consider... |

## `Watch`: `cdk watch`

Shortcut for 'deploy --watch'.

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `stacks` (positional) | `list[str]` | The `STACKS` positional argument. |
| `build_exclude` | `list[str]` | Do not rebuild asset with the given ID. Can be specified multiple times. |
| `change_set_name` | `str` | Name of the CloudFormation change set to create. |
| `concurrency` | `int` | Maximum number of simultaneous deployments (dependency permitting) to execute (default 1). |
| `exclusively` | `bool` | Only deploy requested stacks, don't include dependencies. |
| `force` | `bool` | Always deploy stack even if templates are identical (default false). |
| `hotswap` | `bool` | Attempts to perform a 'hotswap' deployment, but does not fall back to a full deployment if that is not possible. Instead, changes to any... |
| `hotswap_ecs_maximum_healthy_percent` | `int` | Upper limit on the number of your service's tasks that are allowed in the RUNNING or PENDING state during a deployment, as a percentage o... |
| `hotswap_ecs_minimum_healthy_percent` | `int` | Lower limit on the number of your service's tasks that must remain in the RUNNING state during a deployment, as a percentage of the desir... |
| `hotswap_ecs_stabilization_timeout_seconds` | `int` | Number of seconds to wait for a single service to reach stable state, where the desiredCount is equal to the runningCount. |
| `hotswap_fallback` | `bool` | Attempts to perform a 'hotswap' deployment, which skips CloudFormation and updates the resources directly, and falls back to a full deplo... |
| `logs` | `bool` | Show CloudWatch log events from all resources in the selected Stacks in the terminal. 'true' by default, use --no-logs to turn off (defau... |
| `outputs_file` | `str` | Path to file where stack outputs will be written as JSON. |
| `progress` | `T.Literal["bar", "events", "errors-only"]` | Display mode for stack activity events. |
| `rollback` | `bool` | Rollback stack to stable state on failure. Defaults to 'true', iterate more rapidly with --no-rollback or -R. Note: do \*\*not\*\* disabl... |
| `toolkit_stack_name` | `str` | The name of the existing CDK toolkit stack (only used for app using legacy synthesis). |

