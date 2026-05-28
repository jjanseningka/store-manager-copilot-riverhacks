# MCP servers

MCP (Model Context Protocol) servers give the agent tools beyond reading
and editing files: filesystem access outside the workspace, GitHub,
databases, ticket systems, browsers, search.

Registered in `.cursor/mcp.json`. Smallest scope that works.

## Build-order rule

> Add a tool only after a workflow has appeared at least once and you can
> verify its output.

Do not bulk-install servers because they look useful. Every server you
add is more surface area and more attack surface.

## Starter set (low risk)

| Server | Scope | When useful |
|---|---|---|
| `@modelcontextprotocol/server-filesystem` | Local files (scoped to a path) | Reading and writing outside the workspace root |
| `hello-world` (local Python) | One greeting + one add tool | Proves the MCP loop end-to-end with zero credentials |

Both are wired into `.cursor/mcp.json` in this starter. The hello-world
server lives in `mcp-servers/hello-world/`. Keep it while trainees learn,
then delete it once you have real servers in place.

## Common additions

| Server | When useful | Notes |
|---|---|---|
| `@modelcontextprotocol/server-github` | PRs, issues, code search | Needs `GITHUB_PERSONAL_ACCESS_TOKEN`; scope read-only |
| `@modelcontextprotocol/server-git` | Local git history | Multi-repo or history-heavy work |
| Atlassian (Jira / Confluence) | Tracker + wiki | Pin to one workspace |
| Slack | Notifications, lookup | Read-only is enough for most cases |
| Postgres / database | Local-only schema and query | Never connect production from a dev box |
| Browser-use / Playwright | UI testing, screenshots | Heavy; do not auto-load if not needed |
| Stripe / Linear / Notion / etc. | Domain-specific | Add one at a time |

## Writing your own (local) MCP server

`mcp-servers/hello-world/` is a minimal uv project (single `server.py`
plus a `pyproject.toml` that declares deps and the build backend). It
is also a **member of the repo-root uv workspace**, which means it
shares one lockfile (`//uv.lock`) and one supply-chain cutoff with
every other Python project in the repo.

Add a new MCP server by:

1. Creating `mcp-servers/<name>/` with its own `pyproject.toml`
   (just `[project]` + `[build-system]`, no `[tool.uv]`).
2. Adding `"mcp-servers/<name>"` to `[tool.uv.workspace] members` in
   `//pyproject.toml`.
3. Running `uv lock` at the repo root.
4. Wiring it into `.cursor/mcp.json` with `uv run --directory
   mcp-servers/<name> --frozen python server.py`.

See `mcp-servers/hello-world/README.md` for the extension recipe and
when to graduate a server to its own repository.

## Supply-chain hygiene for local MCP servers

The workspace root sets `[tool.uv] exclude-newer` in `//pyproject.toml`
to "today minus 7 days" and `.cursor/mcp.json` launches each server with
`uv run --frozen`. Two effects:

- uv refuses to resolve any package published in the last 7 days
  (most malicious uploads get caught within a week).
- uv refuses to mutate `uv.lock` at runtime, so opening a chat never
  triggers a surprise resolution.

Bump dependencies explicitly with `make refresh-lockfile`. Review the
diff. Commit. The cutoff and lockfile cover every workspace member, so
you only manage one date per repo, not one per MCP server.

## Team vs personal config

Cursor reads MCP config from two places:

| File | Scope | Commit? | Use for |
|---|---|---|---|
| `.cursor/mcp.json` | Project, shared with everyone | Yes | Servers the whole team needs (filesystem, github, project DB) |
| `~/.cursor/mcp.json` | User, private | No (not in repo) | Personal tokens, secret-bearing servers (1Password, paid APIs, prod-read access) |

Rule of thumb: if the server needs a credential your teammate does not
have, it goes in `~/.cursor/mcp.json`. If everyone on the project should
have it on day one, it goes in `.cursor/mcp.json`.

## Configuring a server

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

Rules:

- Never inline a token. Use `${VAR}` and source the variable from
  `.env` (gitignored) or a secrets manager (1Password, Doppler, Vault).
- See `.env.example` for the slots the starter expects.
- Scope the token to read-only when you can.
- For filesystem servers, always pass an explicit path. Default-everywhere
  is not a configuration.

## Verifying a server

1. Restart Cursor. Check **Settings → MCP** for the green dot.
2. In a fresh chat, ask the agent: "List the tools you have available."
3. Confirm the new tool appears, then run one small, read-only call.
4. Only then let the agent use it for write actions.

## See also

- Public MCP server catalogue: https://github.com/modelcontextprotocol/servers
- MCP spec: https://modelcontextprotocol.io/
