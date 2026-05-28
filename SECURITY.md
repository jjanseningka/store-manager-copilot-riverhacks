# Security policy

## Supported versions

This is a starter scaffold. The `main` branch is the only supported
surface. Older tags receive no fixes.

## Reporting a vulnerability

If you find a security issue:

1. **Do not** open a public GitHub issue.
2. **Do** open a private security advisory through the repository's
   *Security* tab on GitHub, or email the maintainers listed in the
   repository description.
3. Include: a minimal reproduction, the affected file or hook or MCP
   server, and the impact you can demonstrate.

We will acknowledge within five working days and aim to ship a fix or
mitigation within thirty.

## Threat model in scope

This repo ships:

- Bash and PowerShell hook scripts that read JSON on stdin and decide
  whether to allow shell commands.
- A local Python MCP server (`mcp-servers/hello-world/`).
- A registered set of MCP servers in `.cursor/mcp.json`.
- A bootstrap script that checks tool versions.

In-scope issues:

- A hook that fails open on input it should block.
- A hook that crashes on adversarial input rather than failing open.
- An MCP server tool that escapes its intended scope.
- A script that executes attacker-controlled input.
- A configuration default that exposes secrets, tokens, or filesystem
  paths the user did not opt into.

## Out of scope

- Vulnerabilities in upstream packages (`mcp`, `@modelcontextprotocol/*`,
  `uv`, `node`). Report those upstream.
- Vulnerabilities in third-party MCP servers a user adds to their own
  `.cursor/mcp.json`.
- Trainee mistakes when extending the scaffold (we cannot guard against
  every fork).

## Supply chain

This repo is a uv workspace. The root `pyproject.toml` sets
`[tool.uv] exclude-newer` to "today minus 7 days" and the shared
`uv.lock` covers every workspace member (currently just
`mcp-servers/hello-world`). `.cursor/mcp.json` launches MCP servers
with `uv run --frozen`. See `mcp-servers/hello-world/README.md` and
`docs/references/mcp-servers.md`. Add new Python projects as workspace
members so they pick up the same cutoff automatically.
