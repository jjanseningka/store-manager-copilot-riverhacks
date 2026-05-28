# Skills

Skills are workflow expertise that load on demand. Unlike `.cursor/rules/`
(always-on context), a skill only enters the agent's context when its
`description` matches the current task.

## Layout

```text
.cursor/skills/
|-- README.md                # this file
`-- <skill-name>/
    |-- SKILL.md             # required - frontmatter + instructions
    |-- reference.md         # optional - longer reference
    `-- scripts/             # optional - executables the skill calls
```

## SKILL.md shape

```markdown
---
name: skill-name
description: One sentence. What it does and when to use it. Include trigger words.
---

# Title

## When to use this

## Steps

## Examples
```

Rules:

- `name` is lowercase, hyphens, max 64 chars.
- `description` is the only thing the agent sees when deciding to load the skill.
  Be specific. Include trigger terms ("commit message", "review PR", "alembic migration").
- Keep `SKILL.md` under 500 lines. Put longer reference in sibling files.

## When to add a skill (vs a rule)

| Need | Put it in |
|---|---|
| Always-on guardrail or convention | `.cursor/rules/*.mdc` with `alwaysApply: true` |
| Task-scoped expertise loaded sometimes | `.cursor/skills/<name>/SKILL.md` |
| One-shot repeatable workflow | `.cursor/commands/<name>.md` |

A useful test: if you would not want the instruction in **every** chat,
it does not belong in an always-on rule. Make it a skill.

## Shipped skills

| Skill | Loads when | Purpose |
|---|---|---|
| `repo-conventions` | The agent needs orientation on this repo's layout | Sample skill — replace with real conventions |
| `create-skill` | The user asks to author a new skill | Meta-skill: how to write a SKILL.md |

## See also

- Cursor skills docs: https://cursor.com/docs/agent/skills
