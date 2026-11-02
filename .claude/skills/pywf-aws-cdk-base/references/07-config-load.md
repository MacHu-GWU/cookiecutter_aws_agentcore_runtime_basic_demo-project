---
description: "How the config is loaded: Config.load dispatches on the runtime, each source is its own load_from_* method that takes what it needs as arguments, and the local source merges four json5 files, with git-ignored secret files and examples. Read when loading the config, adding or changing a config file, adding a config source, or when a config value is missing."
---

# Config Loading

Seed repo: [`config/config_00_main.py`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/cookiecutter_aws_cdk_demo/config/config_00_main.py), [`config/`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/tree/1.0.0/config).

---

## 1. One entry point, one method per source

- `Config.load(env_name, runtime_name)` is the only loader the rest of the code calls (through `one.config`). It branches on the runtime (`02-runtime.md`) and calls one `load_from_<source>` class method per runtime; a runtime with no source raises `NotImplementedError`.
- Each `load_from_<source>` method takes everything it reads from as arguments, such as `dir_config`, with a default for normal use. Tests pass their own; the method never reaches for a global it could have been given.
- In this template only `local` has a source, `load_from_local_config_file`: the project's admin deploys from a local machine.

---

## 2. The local source

`load_from_local_config_file(env_name, dir_config=path_enum.dir_config)` merges four files, a later one overriding the keys of an earlier one:

1. `config-shared.json5`: values of every environment, such as `project_name`.
2. `config-shared-secret.json5`: optional, git-ignored.
3. `config-<env>.json5`: values of one environment, such as `aws_region`.
4. `config-<env>-secret.json5`: optional, git-ignored, such as `aws_account_id`.

Then it sets `env_name` itself. The files are json5, so each value carries a comment saying what it is for.

---

## 3. Keeping the files

- A secret value goes only in a `-secret` file; `.gitignore` covers `config/config-*-secret.json5`.
- `config/example/` holds a `*.json5.example` of each kind of file, with every key and a fake value. Update it with every new field, so a new machine knows what to fill in.
- A new field is added in three places: the model (`04-config-model.md`), the json5 file of every environment that needs it (or the shared one), and its example.
