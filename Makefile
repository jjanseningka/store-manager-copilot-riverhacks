.PHONY: lint test typecheck agent-smoke-check smoke-mcp bootstrap refresh-lockfile pre-commit pre-commit-install

bootstrap:
	./scripts/bootstrap.sh

refresh-lockfile:
	./scripts/refresh-lockfile.sh

pre-commit-install:
	pre-commit install

pre-commit:
	pre-commit run --all-files

# Lint, test, and typecheck targets run against the sample package shipped
# with the scaffold. Each target prints a clear hint if its tool is not on
# PATH so a fresh checkout never hard-fails before bootstrap.

lint:
	@command -v ruff >/dev/null 2>&1 || { echo "ruff not on PATH. Install: 'uv tool install ruff' or 'pipx install ruff'." >&2; exit 1; }
	ruff check src tests mcp-servers

test:
	@command -v pytest >/dev/null 2>&1 || { echo "pytest not on PATH. Install: 'uv tool install pytest' or 'pipx install pytest'." >&2; exit 1; }
	pytest

typecheck:
	@command -v pyright >/dev/null 2>&1 || { echo "pyright not on PATH. Install: 'uv tool install pyright' or 'npm install -g pyright'." >&2; exit 1; }
	pyright

agent-smoke-check:
	./scripts/agent-smoke-check.sh

# End-to-end check for the hello-world MCP server: spawns the server
# via the same uv command .cursor/mcp.json uses, lists its tools, and
# calls each one. Proves the MCP loop works without launching Cursor.
smoke-mcp:
	@command -v uv >/dev/null 2>&1 || { echo "uv not on PATH. Install: 'brew install uv' or 'curl -LsSf https://astral.sh/uv/install.sh | sh'." >&2; exit 1; }
	uv run --frozen python scripts/smoke-mcp.py
