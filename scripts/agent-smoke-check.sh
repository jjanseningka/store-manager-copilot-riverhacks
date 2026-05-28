#!/usr/bin/env bash
set -euo pipefail

# Verify the agent-readiness scaffold is in place.
# Each entry is one slot from the build order: Map -> AGENTS -> Rules ->
# Skills -> MCP -> Hooks -> Sub-agents.

required_files=(
  "AGENTS.md"
  "README.md"
  "Makefile"
  "LICENSE"
  "CHANGELOG.md"
  "CONTRIBUTING.md"
  "SECURITY.md"
  ".editorconfig"
  ".env.example"
  ".gitattributes"
  ".gitignore"
  ".pre-commit-config.yaml"
  ".github/workflows/ci.yml"
  ".github/PULL_REQUEST_TEMPLATE.md"
  ".github/ISSUE_TEMPLATE/bug_report.md"
  ".github/ISSUE_TEMPLATE/feature_request.md"
  ".github/ISSUE_TEMPLATE/config.yml"
  ".cursor/mcp.json"
  ".cursor/hooks.json"
  ".cursor/hooks/block-destructive.sh"
  ".cursor/hooks/block-destructive.ps1"
  ".cursor/hooks/README.md"
  ".cursor/commands/plan.md"
  ".cursor/commands/pr.md"
  ".cursor/plans/README.md"
  ".cursor/rules/000-project-map.mdc"
  ".cursor/rules/010-agent-workflow.mdc"
  ".cursor/rules/020-testing.mdc"
  ".cursor/rules/030-agent-safety.mdc"
  ".cursor/rules/040-python.mdc"
  ".cursor/rules/041-python-tests.mdc"
  ".cursor/skills/README.md"
  ".cursor/skills/repo-conventions/SKILL.md"
  ".cursor/skills/create-skill/SKILL.md"
  "docs/architecture/project-map.md"
  "docs/architecture/architecture.md"
  "docs/architecture/decisions/README.md"
  "docs/architecture/decisions/0001-template.md"
  "docs/knowledge/MEMORY.md"
  "docs/references/mcp-servers.md"
  "docs/references/subagents.md"
  "docs/references/faq.md"
  "docs/references/glossary.md"
  "scripts/bootstrap.sh"
  "scripts/bootstrap.ps1"
  "scripts/agent-smoke-check.ps1"
  "scripts/refresh-lockfile.ps1"
  "scripts/smoke-mcp.py"
  "mcp-servers/hello-world/server.py"
  "mcp-servers/hello-world/README.md"
  "mcp-servers/hello-world/pyproject.toml"
  "mcp-servers/hello-world/.python-version"
  "pyproject.toml"
  "uv.lock"
  "src/README.md"
  "src/sample/__init__.py"
  "src/sample/greeter.py"
  "tests/README.md"
  "tests/conftest.py"
  "tests/sample/test_greeter.py"
)

missing=0
for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "missing: $file" >&2
    missing=1
  fi
done

executable_scripts=(
  ".cursor/hooks/block-destructive.sh"
  "scripts/bootstrap.sh"
  "scripts/agent-smoke-check.sh"
  "scripts/refresh-lockfile.sh"
)

for script in "${executable_scripts[@]}"; do
  if [[ ! -x "$script" ]]; then
    echo "not executable: $script" >&2
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  exit 1
fi

echo "agent starter repo shape ok"
