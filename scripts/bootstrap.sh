#!/usr/bin/env bash
# Verify the local environment can run the agent scaffold.
# Idempotent. Safe to run repeatedly.

set -euo pipefail

ok=0
warn=0
fail=0

check() {
  local label="$1"; local cmd="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "ok   - $label ($cmd: $(command -v "$cmd"))"
    ok=$((ok + 1))
  else
    echo "miss - $label ($cmd not on PATH)"
    fail=$((fail + 1))
  fi
}

check_optional() {
  local label="$1"; local cmd="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "ok   - $label ($cmd)"
    ok=$((ok + 1))
  else
    echo "warn - $label ($cmd not on PATH; optional)"
    warn=$((warn + 1))
  fi
}

echo "Checking required tools..."
check "Node.js"                                node
check "npx (for filesystem MCP)"               npx
check "Bash"                                   bash
check "jq (for hook scripts)"                  jq
check "uv (for hello-world MCP, PEP 723)"      uv

echo
echo "Checking optional tools..."
check_optional "GitHub CLI (for /pr command)"  gh
check_optional "git"                           git
check_optional "pre-commit (local quality gate)" pre-commit
check_optional "ruff (make lint)"              ruff
check_optional "pytest (make test)"            pytest
check_optional "pyright (make typecheck)"      pyright

echo
echo "Checking project files..."
if [[ -f ".env" ]]; then
  echo "ok   - .env exists"
  ok=$((ok + 1))
elif [[ -f ".env.example" ]]; then
  echo "warn - .env missing; copy .env.example and fill in tokens"
  warn=$((warn + 1))
else
  echo "miss - .env.example missing"
  fail=$((fail + 1))
fi

echo
echo "Running scaffold smoke check..."
if ./scripts/agent-smoke-check.sh; then
  ok=$((ok + 1))
else
  fail=$((fail + 1))
fi

echo
if command -v pre-commit >/dev/null 2>&1; then
  if [[ -d ".git" && ! -f ".git/hooks/pre-commit" ]]; then
    echo "Installing pre-commit git hook..."
    pre-commit install
  else
    echo "ok   - pre-commit git hook already installed (or no .git dir yet)"
  fi
else
  echo "warn - pre-commit not installed; run 'uv tool install pre-commit' or 'pip install pre-commit'"
fi

echo
echo "Summary: $ok ok, $warn warn, $fail fail"

if [[ "$fail" -gt 0 ]]; then
  echo
  echo "Next steps:"
  echo "  - Install any 'miss' tools above."
  echo "  - macOS:    brew install node jq uv gh"
  echo "  - Ubuntu:   sudo apt install nodejs npm jq"
  echo "              curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "              curl -fsSL https://cli.github.com/install.sh | bash"
  echo "  - Windows:  use PowerShell with scripts/bootstrap.ps1"
  echo "              or use this script under WSL2 / Git Bash"
  exit 1
fi

if [[ "$warn" -gt 0 ]]; then
  echo
  echo "Optional tools missing. To install the Python dev toolchain in one shot:"
  echo "  uv tool install ruff"
  echo "  uv tool install pytest"
  echo "  uv tool install pyright"
  echo "  uv tool install pre-commit"
  echo "(Each one is a self-contained install; safe to re-run.)"
fi

cat <<'EOF'

Bootstrap complete. Next:

  1. cp .env.example .env  (if you have not yet)
  2. Fill in tokens — see docs/references/mcp-servers.md
  3. Open the repo in Cursor
  4. In a fresh chat, ask: "Read AGENTS.md and tell me what you would do
     to make a small change here."

EOF
