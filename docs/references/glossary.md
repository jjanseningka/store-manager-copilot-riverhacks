# Glossary

Definitions for every layer of an agent-ready repository. Keep this file
short. If a term grows, push the long form into its own reference.

## Agent

A long-running LLM session with tools. In Cursor it is the chat in the
sidebar. In other harnesses it might be Claude Code, Codex CLI, an SDK
loop, or a GitHub Action.

## Sub-agent

A separate agent run spawned by the main agent through the `Task` tool.
Fresh context, often specialised (read-only explorer, shell runner,
browser, CI investigator). See `subagents.md`.

## Harness

The IDE or runtime hosting the agent — Cursor, Claude Code, Codex CLI,
Cursor SDK, custom service. Same model, different harness, often very
different behaviour.

## Map (step 1)

The repo's table of contents. Lives in `docs/architecture/project-map.md`.
Tells the agent which folders own which concerns and which to ignore.

## AGENTS.md (step 2)

The shared, always-loaded context for any agent harness. Project shape,
commands, operating rules, memory pointer. Should stay short
(~50 to 100 lines).

## Rules (step 3)

Always-on instructions that shape behaviour. Live in `.cursor/rules/*.mdc`
with frontmatter (`description`, `globs`, `alwaysApply`). Use for
guardrails and conventions every chat should respect.

## Skills (step 4)

On-demand workflow expertise. Live in `.cursor/skills/<name>/SKILL.md`.
Loaded by the agent when the `description` matches the task. Use for
specialised knowledge that should not crowd every chat.

## Commands (sub-step of rules/skills)

Repeatable user-invoked workflows. Live in `.cursor/commands/<name>.md`,
invoked with `/<name>`. Use for "the canonical way we do X" recipes.

## MCP (step 5)

Model Context Protocol. A standard for giving agents tools beyond
read/edit (filesystem, GitHub, databases, browsers, search). Registered
in `.cursor/mcp.json` (team) and `~/.cursor/mcp.json` (personal). See
`mcp-servers.md`.

## Hooks (step 6)

Deterministic logic around agent events. Live in `.cursor/hooks.json`
and `.cursor/hooks/*`. Use for checks the agent must never skip
(block destructive shell, auto-format on edit, nudge MEMORY.md on stop).

## Memory

Append-only record of agent-session learnings. Lives in
`docs/knowledge/MEMORY.md`. Distinct from architecture decisions: ADRs
record **why we chose X**; MEMORY records **what surprised us yesterday**.

## ADR

Architecture Decision Record. One file per decision in
`docs/architecture/decisions/`. Numbered, append-only, never rewritten.
Supersede with a new ADR.

## Plan

A short written design produced before any non-trivial change. The
`/plan` command in `.cursor/commands/plan.md` enforces the shape.
Substantive plans are saved to `.cursor/plans/<slug>.md` for resume.

## Smoke check

A fast, deterministic verification that the scaffold itself is intact.
`make agent-smoke-check` runs `scripts/agent-smoke-check.sh`. Run it on
every PR that touches `.cursor/`, `AGENTS.md`, or `docs/architecture/`.
