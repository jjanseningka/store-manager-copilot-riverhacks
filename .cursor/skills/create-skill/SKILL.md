---
name: create-skill
description: Author a new skill for this repository. Use when adding a SKILL.md file under .cursor/skills/, or when the user asks how to write a skill, scaffold a skill, or capture a workflow as a skill.
---

# Creating Skills

Skills are workflow expertise loaded on demand. Use this skill when you
are asked to author or refactor any `SKILL.md` under `.cursor/skills/`.

## Before you write anything

Gather these from the user (or infer from context):

1. **Purpose.** What task does the skill help with? One sentence.
2. **Trigger.** Which words or filenames in a chat should make the agent
   load this skill?
3. **Scope.** Is the knowledge specific to this repo or universal? Repo
   skills go in `.cursor/skills/`. Personal skills go in
   `~/.cursor/skills/`.
4. **Inputs and outputs.** What does the skill read? What does it
   produce? A diff? A file? A decision?
5. **Existing patterns.** Is there a near-duplicate skill already? If so,
   extend it rather than duplicate it.

If the user has supplied verbatim wording, use it verbatim. Do not
paraphrase their voice.

## File shape

Skills live one directory per skill, with a single `SKILL.md`:

```text
.cursor/skills/
`-- <skill-name>/
    |-- SKILL.md         # required
    |-- reference.md     # optional, longer reference
    `-- scripts/         # optional, executables the skill calls
```

`SKILL.md` requires YAML frontmatter and a markdown body:

```markdown
---
name: lower-case-with-hyphens
description: One sentence stating WHAT the skill does and WHEN to use it. Include trigger terms.
---

# Title

## When to use

## Steps

## Examples
```

### Frontmatter rules

| Field | Constraint |
|---|---|
| `name` | Lowercase, hyphens only, max 64 chars, unique |
| `description` | Max ~1024 chars, third person, includes WHAT + WHEN |

The description is the **only** thing the agent sees when deciding
whether to load the skill. Make it specific. Vague descriptions never
load.

## Description writing

Two failure modes to avoid:

| Bad | Why | Better |
|---|---|---|
| "Helps with documents" | No trigger terms, no scope | "Extracts tables from PDF files. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction." |
| "I can help you write commits" | First person; agent is choosing a tool, not greeted | "Generates commit messages by analyzing git diffs. Use when the user asks for help writing commits or reviewing staged changes." |

Pattern: **`<verb> <object>. Use when <user phrasing or file context>.`**

## Body writing

- Keep `SKILL.md` under 500 lines. Push longer reference into
  `reference.md` and link to it.
- Do not restate things the agent already knows ("Python is a programming
  language..."). Every line should earn its tokens.
- Show the **default approach** plus one escape hatch. Multiple equivalent
  options confuse the agent.
- Use concrete examples over abstract guidance.

### Set the right degree of freedom

| Task fragility | Use |
|---|---|
| Many valid approaches, judgement-driven | Plain prose |
| Preferred pattern with acceptable variation | Pseudocode / templates |
| Fragile, must be exact | Reference a script in `scripts/` |

## Skill vs rule vs command vs hook

Decide once before writing. The four layers do different jobs.

| Need | Put it in |
|---|---|
| Always-on guardrail or convention | `.cursor/rules/*.mdc` |
| Task-scoped expertise loaded sometimes | `.cursor/skills/<name>/SKILL.md` |
| User-invoked repeatable workflow | `.cursor/commands/<name>.md` |
| Deterministic check that must never be skipped | `.cursor/hooks/` |

Test: would you want this instruction in **every** chat? If no, it is
not a rule. Would the user invoke it explicitly with `/foo`? If yes, it
is a command. Otherwise it is a skill.

## Workflow

1. Confirm the slot is right (skill, not rule/command/hook).
2. Pick the directory name. Lowercase, hyphens, descriptive.
3. Draft the description first. If you cannot write a specific one-liner,
   the skill is not focused enough.
4. Outline the body in headings before filling them in.
5. Add concrete examples or a script if the task is fragile.
6. Verify: file under 500 lines, file references one level deep,
   consistent terminology, no first person, no time-sensitive claims.
7. Test by asking the agent in a fresh chat to perform the task. If it
   does not load the skill, tighten the description.

## Anti-patterns

- **Vague names**: `helper`, `utils`, `things`. Use the verb from the
  description.
- **Time-sensitive claims**: "as of last quarter..." Use a deprecated
  section instead.
- **Inconsistent terminology**: alternating "field", "box", "control".
  Pick one and stick with it.
- **Windows paths**: always use forward slashes in examples.
- **One-skill-fits-all**: if the description has "or" three times, split
  into separate skills.

## Final checklist

- [ ] `name` is lowercase, hyphens, unique
- [ ] `description` is third person, names trigger terms, names the WHEN
- [ ] Body is under 500 lines
- [ ] Examples are concrete
- [ ] Terminology is consistent
- [ ] No first person, no time-sensitive claims
- [ ] Skill is the right slot (not rule, command, or hook)
- [ ] Tested in a fresh chat
