# Project Map

Use this file as the agent's table of contents.

| Path | Purpose | Local commands |
|---|---|---|
| `src/` | Application code, grouped by feature. Ships with the `sample/` placeholder package. | `make lint`, `make typecheck` |
| `tests/` | Automated tests, mirroring `src/` one-to-one. | `make test` |
| `pyproject.toml` | uv workspace root + shared config for `ruff`, `pytest`, `pyright`, and the 7-day `exclude-newer` cutoff. | n/a |
| `uv.lock` | Workspace lockfile covering every member under `mcp-servers/`. | `make refresh-lockfile` |
| `mcp-servers/` | uv workspace members. `hello-world/` proves the MCP loop end-to-end. | `make smoke-mcp`, `make refresh-lockfile` |
| `.cursor/rules/` | Cursor project rules (always-on guardrails). | n/a |
| `.cursor/skills/` | On-demand workflow expertise. | n/a |
| `.cursor/commands/` | Repeatable agent commands (`/plan`, `/pr`). | n/a |
| `.cursor/hooks/` | Deterministic checks around agent events. | n/a |
| `docs/architecture/` | Project map, architecture overview, ADRs. | n/a |
| `docs/knowledge/MEMORY.md` | Append-only learning log. | n/a |
| `docs/references/` | FAQ, glossary, MCP and sub-agent notes. | n/a |
| `scripts/` | Bootstrap, smoke check, lockfile refresh (POSIX + PowerShell). | `make agent-smoke-check` |

## First Files To Read

- `AGENTS.md` for project-wide instructions.
- This file for layout.
- The nearest `.cursor/rules/*.mdc` file for scoped rules.

## Generated Or Noisy Paths

Keep these out of routine agent context:

- `.venv/`
- `node_modules/`
- `dist/`
- `build/`
- coverage output
- lock files unless dependency changes are the task
