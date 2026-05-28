# FAQ

Questions trainees ask in the first week.

## Setup

### What runs on `git commit`?

`bootstrap` installs `pre-commit` if it is available, which wires up:

- file hygiene (trailing whitespace, EOL, merge markers, large files)
- secret scanning (`gitleaks`)
- shell lint and format (`shellcheck`, `shfmt`)
- Python lint and format (`ruff`)
- GitHub Actions lint (`actionlint`)
- the scaffold smoke check, but only when `.cursor/`, `mcp-servers/`,
  `scripts/`, or top-level docs are touched

If a hook fails, the commit is rejected. Read the message, fix, retry.
To bypass once for an emergency: `git commit --no-verify`. To skip a
single hook: `SKIP=gitleaks git commit ...`.

To run the full set on demand: `make pre-commit`.

### How do I bootstrap a fresh checkout?

**macOS, Linux, WSL2, Git Bash:**

```bash
cp .env.example .env
# fill in tokens
./scripts/bootstrap.sh
# optional but recommended — wire up the dev toolchain so make lint/test/typecheck work:
uv tool install ruff && uv tool install pytest && uv tool install pyright
make agent-smoke-check
make smoke-mcp
```

**Native Windows PowerShell:**

```powershell
Copy-Item .env.example .env
# fill in tokens
pwsh ./scripts/bootstrap.ps1
# optional but recommended:
uv tool install ruff; uv tool install pytest; uv tool install pyright
pwsh ./scripts/agent-smoke-check.ps1
```

Then open the repo in Cursor and ask: "Read AGENTS.md and tell me what
you would do to make a small change here." If the answer makes sense,
you are wired up.

### Bootstrap warned about ruff / pytest / pyright. Do I have to install them?

Only if you want `make lint`, `make test`, or `make typecheck` to do
anything. The scaffold itself, the MCP servers, the hooks, and
`make smoke-mcp` all work without them. The recommended install on any
machine that already has `uv`:

```bash
uv tool install ruff
uv tool install pytest
uv tool install pyright
uv tool install pre-commit
```

Each one creates an isolated CLI under `~/.local/bin/` (POSIX) or
`%USERPROFILE%\.local\bin\` (Windows). Safe to re-run; safe to skip.

### I'm on Windows. What works and what doesn't?

The Cursor app, the MCP servers in `.cursor/mcp.json`, the rules, the
skills, the commands, and the architecture docs all work natively on
Windows. The shell tooling has two paths:

| You have | Use |
|---|---|
| WSL2 or Git Bash on PATH | The `.sh` scripts and the default `.sh` hook. Works as-is. |
| Native PowerShell only | The `.ps1` equivalents in `scripts/`, and swap the hook to `.ps1`. |

To swap the hook for native PowerShell, edit `.cursor/hooks.json`:

```jsonc
"command": "pwsh",
"args": ["-NoProfile", "-File", ".cursor/hooks/block-destructive.ps1"]
```

See `.cursor/hooks/README.md` for the full snippet.

Install the toolchain on Windows with:

```powershell
winget install OpenJS.NodeJS astral-sh.uv Microsoft.PowerShell GitHub.cli
```

`make` is not native on Windows. Either install it (`winget install
GnuWin32.Make`) or just call `pwsh ./scripts/<name>.ps1` directly.

### My MCP server has a red dot in Cursor settings. What now?

1. Open **Settings → MCP**. Click the server. Look at stderr.
2. Most red dots are one of three things:
   - missing `npx` or `uvx` on the PATH
   - missing env var (`GITHUB_PERSONAL_ACCESS_TOKEN`, etc.)
   - typo in `command` or `args`
3. After fixing, restart Cursor. MCP changes do not always hot-reload.

### The agent ignores my AGENTS.md.

- Confirm the file is at the repo root, not in a subfolder.
- Confirm the agent's "working directory" is the repo (status bar bottom-left).
- Reload the window. Cursor reads `AGENTS.md` on session start.
- If still ignored: the file may be too long. Trim to under ~100 lines and
  push detail into rules or skills.

## Rules vs skills vs commands vs hooks

### When should I write a rule vs a skill?

| Use a rule when | Use a skill when |
|---|---|
| Every chat needs the instruction | Only some tasks need the instruction |
| Under ~50 lines | Can be ~50 to 500 lines |
| Behaviour or guardrail | Specialised workflow expertise |
| Always-on cost is acceptable | Loading it always would waste context |

If you would not want the instruction in **every** chat, it does not
belong in an always-on rule.

### When should I write a command vs a skill?

- **Command** (`.cursor/commands/foo.md`): the user invokes it explicitly
  with `/foo`. One canonical workflow, run on demand.
- **Skill** (`.cursor/skills/foo/SKILL.md`): the agent decides to load it
  based on the task. Reference material, not a single workflow.

A `/pr` command says "do this exact recipe now." A `creating-prs` skill
says "here is what good PR practice looks like, apply where relevant."

### When should I write a hook vs a rule?

A rule is advisory: the agent might forget. A hook is deterministic: it
runs every time, no matter what the agent decides. Use a hook when
**skipping the check would cause real damage** (destructive commands,
secret exfiltration, missing format-on-save).

## Workflow

### My rule does not seem to apply.

- Check the frontmatter. `alwaysApply: true` is needed unless the rule is
  globbed to specific paths.
- Check `globs:` matches the file the agent is touching.
- Reload the window after editing rule files.
- Test: open a chat, type "@Rule" and pick the rule from the picker. If
  it shows up there, Cursor sees it.

### How do I debug a hook?

1. Open **Settings → Hooks**. Confirm the hook is listed.
2. Open the **Hooks** output channel (`View → Output → Hooks`).
3. Trigger the event manually (run a matching shell command, edit a file).
4. Watch the channel for parse errors, missing binaries, or non-zero exits.
5. If the hook never fires: remove the `matcher`, confirm the base hook
   works, then add the matcher back. Matchers use JavaScript regex, not POSIX.

### My agent runs for ages on a one-line task.

- The first plan is usually too broad. Interrupt and ask for a smaller plan.
- Move broad exploration to a sub-agent (see `subagents.md`). The main
  agent should not be paging through the codebase on every turn.
- Tighten `docs/architecture/project-map.md` so the agent has fewer
  things to look at.

### When should I update MEMORY.md?

Whenever an agent session surfaced a non-obvious lesson. The `stop` hook
in `.cursor/hooks.json` nudges the agent to do this automatically.
Curate weekly: prune entries that have been promoted to a rule, skill,
or hook.

## Safety

### Can I trust public MCP servers?

Treat them as untrusted until proven otherwise.

- Run them with the smallest credential scope that works.
- Prefer read-only first; flip to read-write only when you have a verifier.
- Pin the package version in `.cursor/mcp.json` when stakes are high.
- For anything touching production, run the server locally, not via `npx`.

### Why does the hello-world MCP server use a 7-day-old lockfile?

Supply-chain hygiene. The Python ecosystem (and npm, and others) has a
steady drip of malicious uploads — typosquats, hijacked maintainers,
compromised release pipelines. Most are flagged and yanked within a week.

The repo-root `pyproject.toml` declares a uv workspace and sets
`[tool.uv] exclude-newer = "<today minus 7 days>"`. uv refuses to
install anything published after that date for any workspace member.
`.cursor/mcp.json` launches each MCP server with `uv run --frozen`, so
chats cannot trigger a surprise resolution. Bump explicitly with
`make refresh-lockfile`.

New Python sub-projects (more MCP servers, or your future app) get the
same protection automatically as long as you add them to
`[tool.uv.workspace] members` in `//pyproject.toml`.

### I committed a token. Now what?

1. Rotate the token immediately. Assume it is public.
2. `git filter-repo` or BFG to scrub it from history.
3. Force-push to all remotes that ever saw it.
4. Add a `gitleaks` pre-commit hook so it cannot happen again.
5. Add a line to `MEMORY.md` about it.

### Can the agent run `rm -rf` on me?

The `block-destructive.sh` hook in this starter flags `rm -rf`,
`git push --force`, `terraform destroy`, and similar before they run.
Extend it for whatever your team considers destructive.

## Meta

### Should I check `.cursor/` into git?

Yes, except:

- `.cursor/cache/` — local only.
- `.cursor/plans/` — session-local; already gitignored.
- Personal MCP servers — keep those in `~/.cursor/mcp.json`, not the project.

### Where do I put project-specific docs the agent should always know?

Short version in `AGENTS.md`. Longer reference in `docs/architecture/`
or `docs/references/`, linked from `AGENTS.md` or from a rule.
