# Hooks

Hooks run deterministic logic around agent events: before/after tool calls,
before/after shell execution, before/after file edits, on session start/stop,
etc. They are the way to enforce checks that should never be skipped.

## Layout

```text
.cursor/
|-- hooks.json           # registers hooks for events
`-- hooks/
    `-- *.sh             # the scripts hooks.json points at
```

## When to add a hook

| Need | Use |
|---|---|
| Block destructive commands before they run | `beforeShellExecution` |
| Auto-format after every edit | `afterFileEdit` |
| Inject context after a tool call succeeds | `postToolUse` |
| Audit prompts for secrets before they leave the machine | `beforeSubmitPrompt` |
| Continue a sub-agent loop until a condition holds | `subagentStop` |

Use the **narrowest** event that fits. Do not put behaviour in `sessionStart`
that belongs on `beforeShellExecution`.

## Shape

```json
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [
      { "command": ".cursor/hooks/block-destructive.sh", "failClosed": true }
    ]
  }
}
```

- Project hooks: `.cursor/hooks.json`, paths relative to the project root.
- User hooks: `~/.cursor/hooks.json`, paths relative to `~/.cursor/`.
- Hooks exchange JSON over stdin/stdout. Exit code `2` blocks the action.
- Set `failClosed: true` if the action must be blocked when the hook crashes.

## Samples

### `block-destructive.sh` (command hook on `beforeShellExecution`)

Flags `rm -rf`, `git push --force`, `terraform destroy`, and similar.
Replace it or extend it for the workflows your team actually runs.

A PowerShell-native variant ships alongside it as `block-destructive.ps1`.
Use the `.sh` on macOS, Linux, WSL, and Git Bash. Use the `.ps1` when
running Cursor on native Windows PowerShell. To swap, edit
`.cursor/hooks.json`:

```jsonc
{
  "version": 1,
  "hooks": {
    "beforeShellExecution": [
      {
        "command": "pwsh",
        "args": ["-NoProfile", "-File", ".cursor/hooks/block-destructive.ps1"],
        "failClosed": true
      }
    ]
  }
}
```

Cursor watches `hooks.json` and reloads on save. The `.sh` version uses
`jq`; the `.ps1` version uses native `ConvertFrom-Json` and has no
external dependencies beyond PowerShell 7+.

### `stop` prompt hook — MEMORY.md nudge

Wired in `hooks.json` under the `stop` event. At the end of every agent
turn, the prompt asks the agent itself whether the session deserves a
`docs/knowledge/MEMORY.md` entry, and to append one if so.

Three things make this safe to leave on:

- `type: "prompt"` — the LLM decides; no script to maintain.
- `loop_limit: 1` — without this, every stop triggers a new turn, which
  triggers another stop. Cap it.
- Fail open — there is no `failClosed`, so a broken hook never blocks
  the user.

If the agent starts writing memory entries for trivial chats, tighten
the prompt or move the hook to `sessionEnd` instead of `stop`.

## See also

- Cursor hooks docs: https://cursor.com/docs/agent/hooks
