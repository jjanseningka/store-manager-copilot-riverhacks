---
name: repo-conventions
description: Reference for this repository's layout, naming, and verification commands. Use when the agent needs to learn how this codebase is organized, where to add new files, or which command verifies a change.
---

# Repo Conventions

Replace this sample skill with one that captures real conventions for your
project. It exists to show the shape, not to be kept verbatim.

## When to use this

- The agent is about to add a new file and is unsure where it belongs.
- The agent is about to run a verification command and wants the narrowest one.
- A new contributor or sub-agent needs a quick orientation.

## Layout

- `src/` — application code, grouped by feature.
- `tests/` — mirrors `src/`. One test file per source file.
- `docs/architecture/` — repo map, system diagram, architecture decisions.
- `docs/knowledge/MEMORY.md` — append-only learning log.
- `.cursor/rules/` — always-on rules.
- `.cursor/skills/` — on-demand expertise (this file).
- `.cursor/commands/` — repeatable agent workflows.

## Naming

- Python files: `snake_case.py`.
- TypeScript files: `camelCase.ts` for utilities, `PascalCase.tsx` for components.
- Test files: `test_*.py` or `*.test.ts`.

## Verification

| You changed | Run |
|---|---|
| One file | `make test PATH=<file>` |
| One module | `make test PATH=<module>` |
| Anything | `make lint && make typecheck` |
| Setup itself | `make agent-smoke-check` |

Never claim a change is verified unless one of these commands ran and passed.

## Anti-patterns

- Do not add a new top-level directory without updating `docs/architecture/project-map.md`.
- Do not introduce a new dependency without recording it in the relevant lock file
  and explaining why in the PR body.
- Do not edit generated files in `dist/`, `build/`, or `.venv/`.
