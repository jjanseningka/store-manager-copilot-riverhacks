# agentic-engineering-starter

Bare-minimum, copyable scaffold for making a repository agent-ready in
Cursor or any agentic coding harness. One slot for every layer in the
agentic build order. Brand-neutral, cross-platform, MIT-licensed.

## Get started

Use the green **Use this template** button on GitHub, or clone:

```bash
git clone https://github.com/REPLACE/agentic-engineering-starter.git my-repo
cd my-repo
rm -rf .git && git init        # start fresh history
make bootstrap                  # POSIX (macOS / Linux / WSL / Git Bash)
# or
pwsh ./scripts/bootstrap.ps1    # native Windows PowerShell
```

`make bootstrap` checks tools and runs the scaffold smoke check. It
does *not* install anything for you — but it does print install hints
for whatever is missing.

### What you need installed

| Tier | Tools | Purpose | If missing |
|---|---|---|---|
| Required | `node`/`npx`, `uv`, `bash`, `jq` | filesystem MCP, hello-world MCP, hook scripts | bootstrap fails with install commands |
| Recommended | `ruff`, `pytest`, `pyright`, `pre-commit` | `make lint`/`test`/`typecheck` + git quality gate | bootstrap warns; `make` targets print per-tool hints |
| Optional | `gh` | the `/pr` command | bootstrap warns |

Install the recommended Python dev toolchain (works once `uv` is on PATH —
each `uv tool install` installs one isolated CLI):

```bash
uv tool install ruff
uv tool install pytest
uv tool install pyright
uv tool install pre-commit
```

Or as a single `for` loop:

```bash
for t in ruff pytest pyright pre-commit; do uv tool install "$t"; done
```

After bootstrap is green, follow [First 30 minutes](#first-30-minutes).

## Build order

| Step | Layer | Lives in | Purpose |
|---|---|---|---|
| 1 | Map | `docs/architecture/project-map.md` | Table of contents |
| 2 | AGENTS | `AGENTS.md` | Shared context, always loaded |
| 3 | Rules | `.cursor/rules/*.mdc` | Behaviour, scoped by task |
| 4 | Skills | `.cursor/skills/<name>/SKILL.md` | Expertise, loaded on demand |
| 5 | MCP | `.cursor/mcp.json` (+ `~/.cursor/mcp.json`) | Tools beyond read/edit |
| 6 | Hooks | `.cursor/hooks.json` + `.cursor/hooks/` | Deterministic checks |
| 7 | Sub-agents | `docs/references/subagents.md` | Parallel / isolated work |

Do not skip steps 1 and 2. A powerful agent with no map just burns
context faster.

## File tree

```text
agentic-engineering-starter/
|-- AGENTS.md
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- LICENSE
|-- Makefile
|-- README.md
|-- SECURITY.md
|-- pyproject.toml                     # uv workspace root + shared ruff/pytest/pyright config
|-- .editorconfig
|-- .env.example
|-- .gitattributes
|-- .gitignore
|-- .pre-commit-config.yaml
|-- .github/
|   |-- workflows/ci.yml
|   |-- ISSUE_TEMPLATE/
|   |   |-- bug_report.md
|   |   |-- feature_request.md
|   |   `-- config.yml
|   `-- PULL_REQUEST_TEMPLATE.md
|-- .cursor/
|   |-- mcp.json
|   |-- hooks.json
|   |-- commands/
|   |   |-- plan.md
|   |   `-- pr.md
|   |-- hooks/
|   |   |-- README.md
|   |   |-- block-destructive.sh        # macOS / Linux / WSL / Git Bash
|   |   `-- block-destructive.ps1       # native Windows PowerShell
|   |-- plans/
|   |   `-- README.md
|   |-- rules/
|   |   |-- 000-project-map.mdc
|   |   |-- 010-agent-workflow.mdc
|   |   |-- 020-testing.mdc
|   |   |-- 030-agent-safety.mdc
|   |   |-- 040-python.mdc           # globs **/*.py
|   |   `-- 041-python-tests.mdc     # globs **/test_*.py
|   `-- skills/
|       |-- README.md
|       |-- create-skill/            # meta-skill for authoring SKILL.md files
|       |   `-- SKILL.md
|       `-- repo-conventions/
|           `-- SKILL.md
|-- docs/
|   |-- architecture/
|   |   |-- architecture.md
|   |   |-- project-map.md
|   |   `-- decisions/
|   |       |-- README.md
|   |       `-- 0001-template.md
|   |-- knowledge/
|   |   `-- MEMORY.md
|   `-- references/
|       |-- faq.md
|       |-- glossary.md
|       |-- mcp-servers.md
|       `-- subagents.md
|-- mcp-servers/                         # uv workspace members
|   `-- hello-world/
|       |-- .python-version
|       |-- README.md
|       |-- pyproject.toml
|       `-- server.py
|-- uv.lock                              # shared lockfile for every workspace member
|-- src/
|   |-- README.md
|   `-- sample/                          # placeholder package — rename or replace
|       |-- __init__.py
|       `-- greeter.py
|-- tests/
|   |-- README.md
|   |-- conftest.py
|   `-- sample/
|       `-- test_greeter.py
`-- scripts/
    |-- agent-smoke-check.sh
    |-- agent-smoke-check.ps1            # Windows variant
    |-- bootstrap.sh
    |-- bootstrap.ps1                    # Windows variant
    |-- refresh-lockfile.sh
    |-- refresh-lockfile.ps1             # Windows variant
    `-- smoke-mcp.py                     # drives hello-world over stdio (make smoke-mcp)
```

## First 30 minutes

1. Copy this folder into a real repo.
2. `cp .env.example .env` and fill in any MCP tokens you plan to use.
   On Windows PowerShell: `Copy-Item .env.example .env`.
3. **macOS / Linux / WSL / Git Bash:** `make bootstrap`.
   **Native Windows PowerShell:** `pwsh ./scripts/bootstrap.ps1`.
   Either one verifies tools and runs the smoke check.
4. Install the recommended Python dev toolchain if you skipped it earlier:
   `uv tool install ruff && uv tool install pytest && uv tool install pyright`.
5. Confirm the sample wires up: `make lint && make test && make smoke-mcp`.
   The first two cover the `src/sample/` package. The third spawns the
   `hello-world` MCP server over stdio and calls its tools — proving the
   MCP loop works without launching Cursor. Rename or replace the
   samples once you have real code.
6. Fill `docs/architecture/project-map.md` with the real layout.
7. Fill `docs/architecture/architecture.md` with one diagram and three paragraphs.
8. Replace placeholders in `AGENTS.md`.
9. Keep 2 to 4 Cursor rules. Trim anything you do not use.
10. Edit `.cursor/skills/repo-conventions/SKILL.md` to match this repo.
11. Set `.cursor/mcp.json` to one or two low-risk MCP servers
    (see `docs/references/mcp-servers.md`).
12. Decide whether the `block-destructive.sh` hook is what you want, or replace it.
    On native Windows, swap `hooks.json` to `block-destructive.ps1` —
    see `.cursor/hooks/README.md`.
13. In a fresh Cursor chat, prove the MCP loop:
    > Use the `hello-world` server to greet `Cursor`, then add 17 and 25.
14. Then ask Cursor: "Read AGENTS.md and tell me what you would do to
    make a small change here."

Stuck? Read `docs/references/faq.md` first.

## Operating principles

- Agents need a map before they need more tools.
- Static context belongs in `AGENTS.md` or rules.
- Reusable expertise belongs in skills, not in always-on rules.
- Workflows that repeat belong in `.cursor/commands/`.
- Tool access belongs in MCP, with the smallest scope that works.
- Deterministic checks belong in hooks.
- Verification belongs in commands the agent can call.
- Lessons belong in `MEMORY.md`, append-only.
- Architectural reasoning belongs in `docs/architecture/decisions/`.

## Maintenance rhythm

| When | Action |
|---|---|
| After every agentic session | Append one entry to `MEMORY.md` (the `stop` hook nudges you) |
| After the same PR comment appears twice | Add or update a rule |
| After the same workflow appears three times | Promote it to `.cursor/commands/` |
| After domain expertise outgrows a rule | Move it to `.cursor/skills/` |
| After a workflow must never be skipped | Promote it to `.cursor/hooks/` |
| When you want fresh MCP deps | `make refresh-lockfile` (advances 7-day soak, re-locks) |
| Every month | Remove stale rules and dead commands |
| Every model or harness upgrade | Re-test whether old constraints still help |

## Useful links

- [Cursor Rules docs](https://cursor.com/docs/agent/rules)
- [Cursor Skills docs](https://cursor.com/docs/agent/skills)
- [Cursor Hooks docs](https://cursor.com/docs/agent/hooks)
- [Cursor agent best practices](https://cursor.com/blog/agent-best-practices)
- [Claude Code large-codebase patterns](https://claude.com/blog/how-claude-code-works-in-large-codebases-best-practices-and-where-to-start)
- [AGENTS.md spec](https://agentsmd.io/)
- [Public MCP servers](https://github.com/modelcontextprotocol/servers)

## Design rule

Start small. Add a rule only after the agent repeats the same mistake twice.
Add a tool only after a workflow has appeared at least once and you can
verify its output. Promote a rule to a skill, command, or hook only when
the next layer earns its keep.
