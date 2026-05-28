#!/usr/bin/env bash
# Refresh the workspace lockfile.
#
# Advances `exclude-newer` in the root pyproject.toml (which is the uv
# workspace root) to "today minus 7 days" (UTC) and re-runs `uv lock`.
# The 7-day soak gives the Python ecosystem time to flag malicious
# package versions before we pick them up. The setting applies to every
# workspace member — currently `mcp-servers/hello-world`.
#
# Run when you want to refresh dependencies. Review and commit the diff
# afterwards.

set -euo pipefail

cd "$(dirname "$0")/.."

PYPROJECT="pyproject.toml"

if [[ ! -f "$PYPROJECT" ]]; then
  echo "error: $PYPROJECT not found (expected workspace root)" >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv not on PATH. Install via 'brew install uv' or 'curl -LsSf https://astral.sh/uv/install.sh | sh'" >&2
  exit 1
fi

if date -u -v-7d +"%Y-%m-%dT00:00:00Z" >/dev/null 2>&1; then
  cutoff=$(date -u -v-7d +"%Y-%m-%dT00:00:00Z") # BSD date (macOS)
else
  cutoff=$(date -u -d '7 days ago' +"%Y-%m-%dT00:00:00Z") # GNU date (Linux)
fi

echo "Setting exclude-newer to: $cutoff"

tmp="$PYPROJECT.tmp"
sed "s|^exclude-newer = .*|exclude-newer = \"$cutoff\"|" "$PYPROJECT" >"$tmp"
mv "$tmp" "$PYPROJECT"

echo "Re-locking workspace ..."
uv lock

cat <<'EOF'

Done. Review the changes with:

  git diff -- pyproject.toml uv.lock

Then commit if the diff looks sane.

EOF
