# What changed

One-paragraph summary. Why, not what — the diff already shows what.

## Build-order layer

Which layer does this PR touch? Tick one.

- [ ] Map (`docs/architecture/`)
- [ ] AGENTS (`AGENTS.md`)
- [ ] Rules (`.cursor/rules/`)
- [ ] Skills (`.cursor/skills/`)
- [ ] MCP (`.cursor/mcp.json`, `mcp-servers/`)
- [ ] Hooks (`.cursor/hooks.json`, `.cursor/hooks/`)
- [ ] Sub-agents (`docs/references/subagents.md`)
- [ ] Scaffolding (scripts, CI, templates, docs)

## Verification

- [ ] `make agent-smoke-check` passes locally
- [ ] `pwsh ./scripts/agent-smoke-check.ps1` passes locally (if I have PowerShell)
- [ ] No new vendor or organization names committed
- [ ] If I added a script, both `.sh` and `.ps1` ship together
- [ ] If I added a hook, the README documents the cross-OS swap
- [ ] If I touched the hello-world MCP, I ran `make refresh-lockfile`

## Notes for the reviewer

Anything subtle, surprising, or worth pushing back on.
