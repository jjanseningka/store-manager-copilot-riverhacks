# hello-world MCP server

The smallest useful MCP server. Two tools (`hello`, `add`), one Python
module, locked dependencies with a 7-day soak window.

## Why this exists

To prove the loop end-to-end:

1. Cursor launches `server.py` via `uv run --frozen`.
2. The agent sees `hello` and `add` in its tool list.
3. The agent calls one of them.
4. You read the response in chat.

Once this works, you have everything you need to write a real MCP server
for your domain.

## Layout

```text
mcp-servers/hello-world/
|-- pyproject.toml      # deps + build-system + project metadata
|-- .python-version     # 3.11 pin
|-- server.py           # FastMCP server + tools
`-- README.md
```

This directory is a member of the repo-root uv workspace. The shared
lockfile (`//uv.lock`) and the supply-chain cutoff (`exclude-newer` in
`//pyproject.toml`) cover every MCP server in `mcp-servers/`.

## Supply-chain hygiene: the 7-day rule

The workspace root sets `[tool.uv] exclude-newer` to a UTC date 7 days
behind today. uv refuses to resolve any package published after that
date, even if a newer version exists.

The reasoning: most malicious PyPI uploads (`colorama`-style
typosquats, hijacked maintainers, compromised release pipelines) get
yanked or flagged within a week. A 7-day delay turns that race in our
favour without giving up patch updates entirely.

`.cursor/mcp.json` runs the server with `uv run --frozen`. That refuses
to update `uv.lock` at runtime, so opening a chat never triggers a
surprise resolution. The only way new versions enter the tree is the
explicit refresh below.

## Refreshing dependencies

From the repo root:

```bash
make refresh-lockfile
```

This bumps `exclude-newer` in `//pyproject.toml` to "today minus 7 days"
and re-runs `uv lock` at the workspace root. Review the diff, sanity-
check the new versions, commit.

Do not edit `uv.lock` by hand.

## Run it standalone

```bash
uv run --directory mcp-servers/hello-world --frozen python server.py
```

The process listens on stdio. Press `Ctrl+C` to stop. Useful for
debugging without launching Cursor.

## Try it from Cursor

Open a fresh chat:

> Use the `hello-world` server to greet `Cursor`, then add 17 and 25.

The agent should call both tools and show their return values.

If it does not see the tools: **Settings → MCP**, click the
`hello-world` server, read stderr. Most failures are a missing `uv` on
PATH or a stale `.venv` (delete `//.venv` and let uv recreate it; uv
workspaces share one venv at the workspace root).

## Add your own tool

Edit `server.py`:

```python
@mcp.tool()
def reverse(text: str) -> str:
    """Reverse a string."""
    return text[::-1]
```

Save. Restart Cursor (MCP changes do not always hot-reload). The new
tool appears in the agent's tool list.

If your tool needs a new package, add it to `pyproject.toml` under
`dependencies`, then `make refresh-lockfile`.

## When to outgrow this

Promote to its own repository when:

- You have more than ~5 tools.
- Tools share helper code worth importing.
- You want CI to test the server.
- You want to publish the server for the team to reuse.

Until then, one file is fine. To detach the server from the workspace
later: copy the directory out, re-add `[tool.uv]` (with its own
`exclude-newer`) to the standalone `pyproject.toml`, run `uv lock`, and
remove the entry from `//pyproject.toml`'s `[tool.uv.workspace]`.
