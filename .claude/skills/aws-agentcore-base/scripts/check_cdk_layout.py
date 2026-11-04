#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare the project's agentcore/cdk/ with what the installed AgentCore CLI's `agentcore create` writes."""

from __future__ import annotations

import argparse
import difflib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

#: Not part of the template: build output and installed dependencies.
IGNORED_PARTS = {"node_modules", "cdk.out", "dist", ".cdk.staging"}

#: Written by `npm install`, which the fresh project skips.
IGNORED_FILES = {"package-lock.json"}

#: Files the project extends: every code line of the template must still be
#: there, in order; the project may add lines and drop comments.
EXTENDED_FILES = {"lib/cdk-stack.ts"}


def list_files(dir_root: Path) -> set[str]:
    """Paths of the template-relevant files under ``dir_root``, relative, with ``/``."""
    files = set()
    for path in dir_root.rglob("*"):
        rel = path.relative_to(dir_root)
        if path.is_file() and not IGNORED_PARTS.intersection(rel.parts):
            if rel.name not in IGNORED_FILES:
                files.add(rel.as_posix())
    return files


def code_lines(text: str) -> list[str]:
    """The stripped lines of TypeScript source that are neither blank nor ``//`` comments."""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("//"):
            lines.append(line)
    return lines


def is_extension_of(template: str, project: str) -> bool:
    """Whether every code line of ``template`` appears in ``project``, in the same order."""
    project_lines = iter(code_lines(project))
    return all(line in project_lines for line in code_lines(template))


def create_fresh_project(agentcore: str, dir_parent: Path) -> Path:
    """Run ``agentcore create`` in ``dir_parent`` (outside any project); return its ``agentcore/cdk``."""
    subprocess.run(
        [agentcore, "create", "--name", "LayoutCheck", "--skip-install", "--skip-git"],
        cwd=dir_parent,
        check=True,
        capture_output=True,
        text=True,
    )
    return dir_parent / "LayoutCheck" / "agentcore" / "cdk"


def compare(dir_template: Path, dir_project: Path) -> list[str]:
    """Every difference between the template's and the project's ``agentcore/cdk``, as report lines."""
    problems = []
    template_files = list_files(dir_template)
    project_files = list_files(dir_project)
    for rel in sorted(template_files - project_files):
        problems.append(f"MISSING: {rel} is in the template, not in the project")
    for rel in sorted(project_files - template_files):
        problems.append(f"EXTRA: {rel} is in the project, not in the template")
    for rel in sorted(template_files & project_files):
        template = (dir_template / rel).read_text(encoding="utf-8")
        project = (dir_project / rel).read_text(encoding="utf-8")
        if template == project:
            continue
        if rel in EXTENDED_FILES and is_extension_of(template, project):
            continue
        diff = difflib.unified_diff(
            template.splitlines(),
            project.splitlines(),
            fromfile=f"template/{rel}",
            tofile=f"project/{rel}",
            lineterm="",
        )
        problems.append(f"CHANGED: {rel}\n" + "\n".join(diff))
    return problems


def _main(project_root: Path, agentcore: str, keep: bool = False) -> int:
    """Create a fresh project with the installed CLI in a temporary directory, and
    compare its ``agentcore/cdk/`` with the project's.

    Expected: the same files with the same content, except ``package-lock.json``
    (only written by ``npm install``) and ``lib/cdk-stack.ts``, which may add
    lines (``bind()``) as long as every code line of the template is still there.
    Anything else is drift: after upgrading the CLI, apply the template's change
    to the project, or run ``agentcore migrate``.

    Returns 0 when there is no drift, 1 when there is, or when the CLI fails.
    """
    dir_project = project_root / "agentcore" / "cdk"
    if not dir_project.is_dir():
        print(f"ERROR: {dir_project} not found", file=sys.stderr)
        return 1
    if shutil.which(agentcore) is None and not Path(agentcore).exists():
        print(
            f"ERROR: AgentCore CLI {agentcore!r} not found; run through mise",
            file=sys.stderr,
        )
        return 1
    dir_temp = Path(tempfile.mkdtemp(prefix="agentcore-layout-"))
    try:
        try:
            dir_template = create_fresh_project(agentcore, dir_temp)
        except subprocess.CalledProcessError as e:
            print(
                f"ERROR: agentcore create failed:\n{e.stdout}{e.stderr}",
                file=sys.stderr,
            )
            return 1
        problems = compare(dir_template, dir_project)
    finally:
        if keep:
            print(f"Kept the fresh project in {dir_temp}")
        else:
            shutil.rmtree(dir_temp, ignore_errors=True)
    if not problems:
        print(f"OK: {dir_project} matches the template of the installed AgentCore CLI")
        return 0
    for problem in problems:
        print(problem)
    print(f"{len(problems)} difference(s) from the template")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_cdk_layout",
        description="Compare agentcore/cdk/ with a fresh `agentcore create` of the installed CLI.",
    )
    parser.add_argument(
        "--project_root",
        type=Path,
        default=Path.cwd(),
        help="the folder that holds agentcore/ (default: the current directory)",
    )
    parser.add_argument(
        "--agentcore",
        default="agentcore",
        help="the AgentCore CLI executable (default: agentcore on PATH)",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="keep the fresh project, to inspect it",
    )
    args = parser.parse_args(argv)
    return _main(
        project_root=args.project_root, agentcore=args.agentcore, keep=args.keep
    )


if __name__ == "__main__":
    sys.exit(main())
