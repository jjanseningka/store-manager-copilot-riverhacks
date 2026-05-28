# Agent Instructions

## Project Shape

- `src/` contains application code.
- `tests/` mirrors `src/`.
- `docs/architecture/project-map.md` is the table of contents.
- `docs/architecture/architecture.md` is the system overview.
- `docs/architecture/decisions/` records why things are the way they are.
- `docs/knowledge/MEMORY.md` records agent-session learnings.
- `docs/references/` holds curated MCP and sub-agent notes.

## Agent context layers

- `.cursor/rules/` — always-on behaviour rules.
- `.cursor/skills/` — workflow expertise loaded on demand.
- `.cursor/commands/` — repeatable agent workflows (`/plan`, `/pr`).
- `.cursor/mcp.json` — registered MCP tools.
- `.cursor/hooks.json` — deterministic checks around agent events.

## Commands

- `make lint` checks style.
- `make test` runs the narrow test suite.
- `make typecheck` runs static checks.
- `make agent-smoke-check` verifies the agent setup.

## Operating Rules

- Start in the folder you are changing, not always the repo root.
- Read `docs/architecture/project-map.md` before broad exploration.
- For "why is this like this?" questions, check `docs/architecture/decisions/`.
- Use the narrowest relevant test or lint command after edits.
- Prefer existing helpers and patterns before adding abstractions.
- Never introduce secrets, generated files, or vendor code into agent context.
- Separate exploration from editing: send long lookups to a sub-agent.

## Memory

Before large changes, skim `docs/knowledge/MEMORY.md`.

After an agentic session, append:

- what was attempted
- what worked
- what failed
- what rule, skill, or hook would have prevented the failure
