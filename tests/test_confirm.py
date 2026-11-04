# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.confirm import confirm
from cookiecutter_aws_agentcore_runtime_basic_demo.confirm import main

import pytest


def answer(text):
    def read(prompt):
        return text

    return read


def no_input(prompt):
    raise EOFError


@pytest.fixture(autouse=True)
def no_skip_vars(monkeypatch):
    monkeypatch.delenv("CONFIRM_YES", raising=False)
    monkeypatch.delenv("CONFIRMED_BY_CHAIN", raising=False)


@pytest.mark.parametrize(
    "read, expected",
    [
        (answer("y"), True),
        (answer("Y"), True),
        (answer("yes"), True),
        (answer(" YES \n"), True),
        (answer(""), False),  # a bare Enter is no
        (answer("n"), False),
        (answer("ye"), False),
        (answer("yess"), False),
        (no_input, False),  # no terminal, such as CI
    ],
)
def test_confirm(read, expected):
    assert confirm("Destroy?", read=read) is expected


def test_confirm_skip_vars(monkeypatch):
    monkeypatch.setenv("CONFIRMED_BY_CHAIN", "true")
    # only the variables passed count
    assert confirm("Destroy?", read=no_input) is False
    assert confirm("Destroy?", ("CONFIRM_YES", "CONFIRMED_BY_CHAIN"), no_input)
    monkeypatch.setenv("CONFIRM_YES", "1")  # only "true" counts
    assert confirm("Destroy?", read=no_input) is False
    monkeypatch.setenv("CONFIRM_YES", "true")
    assert confirm("Destroy?", read=no_input) is True


def test_main(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "yes")
    assert main(["--action", "Destroy?"]) == 0
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert main(["--action", "Destroy?"]) == 1
    assert "Stopped" in capsys.readouterr().err
    monkeypatch.setenv("CONFIRMED_BY_CHAIN", "true")
    args = ["--action", "Destroy?", "--skip_var", "CONFIRMED_BY_CHAIN"]
    assert main(args) == 0


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.confirm",
        preview=False,
    )
