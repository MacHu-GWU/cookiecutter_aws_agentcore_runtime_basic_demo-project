# -*- coding: utf-8 -*-

"""
Ask yes or no before a task changes or destroys something, such as
``ac-down-<env>``: only ``y`` or ``yes`` (any case) goes on; anything else, a
bare Enter, or no terminal at all means no. mise's own ``confirm`` takes a bare
Enter as yes, so it is never used. Run it as the first command of a task:
``.venv/bin/python .mise/tasks/confirm.py --action "<what will happen>"``.

The question is printed as whole lines, flushed, before the answer is read. mise
forwards a task's output line by line (with a ``[task]`` prefix when several
tasks run), so a question without a final newline could stay hidden; whole
lines show at once, and the task needs no ``raw = true``.
"""

from __future__ import annotations

import os
import sys
import argparse

#: Set to ``true`` to answer yes without asking, such as in CI.
CONFIRM_YES_VAR = "CONFIRM_YES"

#: Set to ``true`` by a chain task that has asked already, so that its steps do
#: not ask again; pass it with ``--skip_var`` in those steps.
CONFIRMED_BY_CHAIN_VAR = "CONFIRMED_BY_CHAIN"

#: The answers that mean yes, compared in lower case.
YES_ANSWERS = ("y", "yes")


def confirm(
    action: str,
    skip_vars: tuple[str, ...] = (CONFIRM_YES_VAR,),
    read=None,
) -> bool:
    """
    Whether the user answers yes to ``action``.

    :param action: what will happen, shown in the question.
    :param skip_vars: environment variables that, set to ``true``, answer yes
        without asking.
    :param read: reads the answer; ``input`` when ``None``.
    """
    for var in skip_vars:
        if os.environ.get(var) == "true":
            print(f"{action}\n{var}=true: yes, without asking")
            return True
    if read is None:
        read = input
    print(f"{action}\nType y or yes to go on, anything else stops:", flush=True)
    try:
        answer = read("")
    except EOFError:  # no terminal, such as CI
        answer = ""
    return answer.strip().lower() in YES_ANSWERS


def main(args: list[str] | None = None) -> int:
    """
    ``confirm.py --action <text> [--skip_var <VAR> ...]``: exit 0 on yes, else 1.
    """
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--action", required=True, help="what will happen")
    parser.add_argument(
        "--skip_var",
        action="append",
        default=None,
        help=f"an env var that, set to true, answers yes (default: {CONFIRM_YES_VAR}); repeat",
    )
    parsed = parser.parse_args(args)
    skip_vars = tuple(parsed.skip_var) if parsed.skip_var else (CONFIRM_YES_VAR,)
    if confirm(parsed.action, skip_vars=skip_vars):
        return 0
    print("Stopped: not confirmed", file=sys.stderr)
    return 1
