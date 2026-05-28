# Sub-agents

Sub-agents are separate agent runs spawned by the main agent through the
`Task` tool. They have a fresh context window and can be specialised
(read-only explorer, shell runner, browser-use, code reviewer, etc.).

## When to use a sub-agent

| Need | Sub-agent |
|---|---|
| Broad codebase exploration without polluting main context | read-only explorer |
| Run a long shell or build in parallel | shell |
| Investigate a failing CI check | CI investigator |
| Drive a browser for testing | browser-use |
| Try several approaches in isolated worktrees | best-of-N runner |

The rule of thumb: **separate exploration from editing**. The main agent
keeps the conversation and decides what to edit. Sub-agents do the bulk
research and report back a short summary.

## Patterns

### Parallel exploration

Launch multiple read-only explorers in the same turn when you can split the
question into independent pieces:

- "Where are auth dependencies defined?"
- "Where are auth dependencies consumed?"
- "Where are auth-related tests?"

Each returns a short summary. The main agent synthesises.

### Background long-running work

Run a flaky test suite, a `terraform plan`, or a large build in the
background. Continue talking to the user while it runs. Re-check when the
completion notification arrives.

### Isolated experiments

Use a best-of-N runner for any task where you want to try two or three
approaches and pick the best, without one attempt leaking changes into
another.

## What does not belong in a sub-agent

- Anything you can answer with one `Read` or one `Grep`.
- Anything that depends on the main conversation state. Sub-agents do not
  see the user's previous messages.
- Anything the user has explicitly asked you to do step-by-step.

## See also

- Cursor Task / sub-agent docs: https://cursor.com/docs/agent/sub-agents
