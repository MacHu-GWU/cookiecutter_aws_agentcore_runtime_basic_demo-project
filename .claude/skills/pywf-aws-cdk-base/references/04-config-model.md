---
description: "The Config model: the single source of truth for the settings of one environment, a pure-data pydantic class with no IO, how its fields are written, and how it grows through numbered mixins. Read before adding or changing a config field, or when deciding whether a value belongs in the config."
---

# Config Model

Seed repo: [`config/config_00_main.py`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/cookiecutter_aws_cdk_demo/config/config_00_main.py).

---

## 1. The single source of truth

Every setting that differs per environment or that more than one module needs is a field of `Config`, in `<package_name>/config/`. Code reads it from the config, never from a constant of its own or from `os.environ`. Import it from `<package_name>/config/api.py`.

---

## 2. Pure data

`Config` is a pydantic `BaseModel` describing **what** the settings are. Defining it does no IO; reading the values from somewhere is a separate step (loading), so the same model works whatever the values come from. Tests build it directly with fixed values: `Config(project_name="my_project", env_name="dev", ...)`.

---

## 3. Fields

- One field per line, `name: type = Field()  #: what it is`, fenced by `# fmt: off` / `# fmt: on`.
- Required fields: `project_name`, `env_name` (set by the loader, not by the files), `aws_account_id`, `aws_region`. Add your own after them.
- A secret value, such as `aws_account_id`, is an ordinary field; only where its value is stored differs.

---

## 4. Growing the model

Put a group of related values or derived properties in a numbered module, `config_0N_<topic>.py`, as a mixin class, and add it to the bases of `Config`. The number gives the reading order: a lower module is more basic. `config_01_name.py` is the first such mixin.
