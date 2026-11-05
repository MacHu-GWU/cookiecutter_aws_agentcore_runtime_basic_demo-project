---
name: operation-oriented-design
description: A high-level pattern for code architecture that organizes a codebase around the operations people perform on it again and again (OP), each with one entry point (EP), a predictable footprint (FP), and named commands (CMD). Use when designing or refactoring code architecture, deciding where new code should live, or writing the SOP.md that documents a codebase's operations.
---

# Operation-Oriented Design

## What this is

A set of guiding principles for code architecture, not a rulebook. It does not prescribe file names, directory layouts, or frameworks. It describes what a well-organized codebase should make easy and leaves the concrete layout to the nature of each project.

Every path, task name, and OP title in this document is an illustration. Do not copy them. Derive names and structure from the project's own language, framework, and existing conventions.

## Why: start from the SOP

Quality comes from standardization. Management calls this the SOP, the Standard Operating Procedure. The O in SOP is the OP in this document.

Breaking work into standard, named operations is the core skill of engineering. AI shifts the balance here. It can absorb enormous complexity and search a codebase in seconds, but people cannot. For a system to stay understandable to the humans who own it, it has to compress into a short list of operations a person can recall from common sense. Goals like security, testing, and drift detection don't need frameworks of their own. They show up as operations on the list.

## Core concepts

| Term | Meaning |
|---|---|
| **OP** | Operation. Something people do to the project again and again, describable in a sentence or two. OPs nest: a broad OP contains narrower sub-OPs. |
| **EP** | Entry point. The first file to open for an OP. Usually one file, and thin: it wires things together and calls into real code. Following its imports leads to everything the OP involves. |
| **FP** | Footprint. The files an OP touches. Often several, and can be written as glob patterns. The substantive source code lives here. |
| **CMD** | Command. How you run, verify, or ship the OP. Usually a few commands. |

Commands:

- Prefer mise tasks. When the logic outgrows a one-liner, move it into a project CLI and have the mise task call that CLI.
- Sub-OPs of the same OP share a task prefix, such as `<op>-<action>`, so related tasks group together.
- When an OP needs many similar tasks (one per stack, function, or job), generate them with a script that loops over the targets. Generated tasks stay consistent; hand-written ones drift.

## Principles

1. **List OPs before designing structure.** Derive them from what the project is, not from a template. Directories, modules, commands, and docs then follow the list.
2. **Keep EPs thin.** Put core logic in library code that unit tests can reach.
3. **Keep FPs small and predictable.** If one OP edits files scattered across the repo, the structure is wrong. Fix it before adding more code.
4. **Keep OPs from colliding.** Running one OP should not touch another OP's FP. Pull shared code into its own module and give it an owner OP.
5. **Give every OP at least one verifying CMD.** Commands live in tasks, not in long snippets inside docs.
6. **Organize docs by OP.** A reader should need only the doc for the OP at hand.
7. **Classify new work first.** If it belongs to an existing OP, reuse that OP's EP, FP, and CMD. If not, add a new OP and fill in all three.

## Project types

The OP list depends on what the project is. Most projects are one of these types or a mix of them, and each type brings its own natural set of OPs.

Primary:

- **Python library.** An installable package, often shipping a CLI.
- **Infrastructure as code.** AWS CDK.
- **Serverless.** Lambda, Step Functions, DynamoDB.
- **Agentic application.** Deployed on AWS AgentCore.
- **Web app.** Next.js on Vercel, a FastAPI backend, Neon Postgres, AWS for storage and other services.

Secondary:

- **Data pipeline.** Spark jobs on AWS Glue.
- **Containers.** AWS Fargate.
- **Traditional app.** EC2 with RDS.

## SOP.md

Each project keeps one `SOP.md` that lists every OP. The format is loose. Roughly:

```markdown
# SOP

## OP-1 <Broad operation>
<One or two sentences on what it is.>

- EP: `<path/to/thin_entry_file>`
- FP: `<package>/<area>/**`, `tests/<area>/**`
- CMD: `mise run <op>:check`

### OP-1-1 <Narrower operation>
<One sentence.>

- FP: <only what differs from OP-1>
- CMD: `mise run <op>:<action>`
```

For instance, in a CDK project OP-1 might be "Infrastructure" with `app.py` as its EP, and OP-1-1 might be "Add a stack."

- H2 headings are `OP-N`. H3 headings are sub-OPs, `OP-N-M`. Small actions don't need their own heading; fold them into the parent.
- Sub-OPs inherit from their parent and list only what differs.
- When an OP needs a detailed explanation, write a separate doc that opens with "Implements OP-1-1" and expands on its EP, FP, and CMD. Keep `SOP.md` itself a short index.
- Detailed docs live in agent skill references, indexed by `llms.txt`, so people and agents read the same source.

## Anti-patterns

- Business logic inside the EP, out of reach of unit tests.
- Related code spread across many directories, so every change misses a spot.
- Key commands that exist only in someone's memory or in a long README paragraph.
- Docs organized by date or by module, so doing one thing means reading everything.
