# Changelog

All notable changes to this scaffold are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `.pre-commit-config.yaml` with file-hygiene, gitleaks, shellcheck/shfmt,
  ruff, actionlint, and a local hook that runs the scaffold smoke check
  when `.cursor/`, `mcp-servers/`, `scripts/`, or top-level docs change.
- `make pre-commit` and `make pre-commit-install` targets.
- Bootstrap scripts auto-install the git hook when `pre-commit` is on PATH.
- CI gains a `pre-commit` job that runs `pre-commit run --all-files`.
- `src/sample/` placeholder Python package and matching `tests/sample/`
  so `make lint`, `make test`, and `make typecheck` have something real
  to run against on day one.
- Root `pyproject.toml` as a uv **virtual workspace root** with shared
  config for `ruff`, `pytest`, and `pyright`. Carries the 7-day
  `exclude-newer` cutoff for every workspace member.
- Workspace-root `uv.lock` covering every member under `mcp-servers/`.
- Smoke check (`.sh` + `.ps1`) now requires the sample `src/`, `tests/`,
  workspace-root `uv.lock`, and `scripts/smoke-mcp.py` so forks cannot
  silently lose them.
- `scripts/smoke-mcp.py` end-to-end smoke for the hello-world MCP
  server. Spawns it via the same `uv run --directory ... --frozen`
  command `.cursor/mcp.json` uses, lists tools, calls `hello("Cursor")`
  and `add(17, 25)`, asserts the responses.
- `make smoke-mcp` target wired to the script. CI runs it on every push.
- `bootstrap.sh`/`.ps1` now check for `ruff`, `pytest`, and `pyright` as
  optional tools and print a `uv tool install ...` hint when missing.
- README "Get started" gained a what-you-need-installed table and a
  pointer to `uv tool install ruff/pytest/pyright/pre-commit`.
- FAQ entry "Bootstrap warned about ruff / pytest / pyright. Do I have
  to install them?"

### Changed
- `make lint`, `make test`, and `make typecheck` now invoke `ruff`,
  `pytest`, and `pyright` respectively (and print an install hint when
  the tool is missing) instead of the previous `echo` placeholders.
- `mcp-servers/hello-world/` is now a uv workspace member. The
  `[tool.uv]` block, the per-MCP `uv.lock`, and the per-MCP
  `exclude-newer` cutoff have moved up to the workspace root. Launching
  via `uv run --directory mcp-servers/hello-world --frozen` is unchanged.
- `make refresh-lockfile` rewrites `exclude-newer` in `//pyproject.toml`
  and re-locks the workspace as a whole (one cutoff, one lockfile).
- CI step `Verify hello-world MCP locks resolve frozen` → `Verify
  workspace lockfile is up to date` (now `uv lock --check` at root).

## [0.1.0] - 2026-05-26

### Added
- Initial scaffold covering all seven layers of the agentic build order:
  Map, AGENTS, Rules, Skills, MCP, Hooks, Sub-agents.
- `AGENTS.md`, `README.md`, `Makefile`, `.env.example`, `.gitignore`.
- `.cursor/rules/` with four always-on rules (project-map, workflow,
  testing, safety) and two glob-scoped Python rules.
- `.cursor/skills/` with `repo-conventions` (sample) and `create-skill`
  (meta-skill).
- `.cursor/commands/{plan,pr}.md`.
- `.cursor/hooks.json` + bash and PowerShell variants of
  `block-destructive` hook + `stop` prompt hook for `MEMORY.md` nudges.
- `.cursor/plans/` directory for the `/plan` command.
- `mcp-servers/hello-world/` — local Python MCP server with two tools,
  uv project, 7-day `exclude-newer` supply-chain soak, `--frozen` runtime.
- `docs/architecture/` — project-map, architecture overview, ADR scaffold.
- `docs/knowledge/MEMORY.md` — append-only learning log.
- `docs/references/` — `mcp-servers.md`, `subagents.md`, `faq.md`,
  `glossary.md`.
- `scripts/{bootstrap,agent-smoke-check,refresh-lockfile}.{sh,ps1}` —
  POSIX and PowerShell variants for cross-OS support.
- `LICENSE` (MIT), `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`.
- `.gitattributes`, `.editorconfig`.
- `.github/workflows/ci.yml` — Linux + Windows + macOS smoke matrix.
- `.github/PULL_REQUEST_TEMPLATE.md`, `.github/ISSUE_TEMPLATE/*`.

[Unreleased]: https://github.com/REPLACE/agentic-engineering-starter/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/REPLACE/agentic-engineering-starter/releases/tag/v0.1.0
