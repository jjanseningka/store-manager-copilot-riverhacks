# Contributing

Thanks for considering a change. This repo is a starter scaffold for
making any codebase agent-ready. Keep changes small, opinionated, and
applicable to most repositories — not to any one team's stack.

## Ground rules

- **Brand-neutral.** No vendor or organization names in any committed
  file. Trainees fork this and add their own.
- **One layer at a time.** A PR adds Map *or* Rules *or* Skills *or*
  MCP *or* Hooks *or* Sub-agents — not all of them.
- **Smallest correct change.** If a placeholder is enough, ship a
  placeholder. The starter is a frame, not a full house.

## Local workflow

```bash
cp .env.example .env
make bootstrap            # Linux / macOS / WSL / Git Bash
# OR
pwsh ./scripts/bootstrap.ps1  # native Windows PowerShell
```

`bootstrap` installs the local `pre-commit` git hook if `pre-commit` is
on PATH. From that point on, every `git commit` runs:

- file hygiene (whitespace, EOL, large files, merge conflict markers)
- secret scanning (`gitleaks`)
- shell lint and format (`shellcheck`, `shfmt`)
- Python lint and format (`ruff`)
- GitHub Actions lint (`actionlint`)
- the agent scaffold smoke check (only when scaffold files change)

Run the full set on demand:

```bash
make pre-commit                      # = pre-commit run --all-files
make agent-smoke-check               # just the scaffold check
pwsh ./scripts/agent-smoke-check.ps1 # PowerShell variant
```

CI runs `pre-commit run --all-files` on Ubuntu and the smoke check on
Ubuntu + Windows + macOS. Don't merge a red build.

### Updating pre-commit hook revisions

Apply the same 7-day soak rule as runtime deps:

```bash
pre-commit autoupdate
git diff -- .pre-commit-config.yaml  # review the bumps
make pre-commit                       # confirm hooks still pass
```

Commit `.pre-commit-config.yaml` with a one-line message describing
which revs moved.

## Adding a new layer entry

| You added | Also do |
|---|---|
| A rule under `.cursor/rules/` | Update `scripts/agent-smoke-check.{sh,ps1}` to require it |
| A skill under `.cursor/skills/` | Add to the table in `.cursor/skills/README.md` |
| A hook under `.cursor/hooks/` | Add the swap snippet for the other OS in `.cursor/hooks/README.md` |
| A script under `scripts/` | Ship both `.sh` and `.ps1` variants |
| An MCP server under `mcp-servers/` | Add a README explaining run-standalone, the supply-chain stance, and how to extend |

## Style

- **Prose**: short sentences, present tense, second person.
- **Tables**: prefer over bullet-lists when comparing options.
- **Code blocks**: tagged with the language; never bare backticks.
- **Paths**: forward slashes everywhere (Windows accepts them).

## What to avoid

- Time-sensitive copy ("as of Q3 2025...") — use a "deprecated" section instead.
- Adding deps to `mcp-servers/hello-world/pyproject.toml` without running
  `make refresh-lockfile` afterwards.
- Renaming top-level files without updating the smoke check.
- Vendor-specific examples in any committed Markdown.

## Reporting bugs and ideas

Use the issue templates under `.github/ISSUE_TEMPLATE/`. Keep titles
specific: "smoke check fails on macOS-arm64 with bash 3.2", not "broken".
