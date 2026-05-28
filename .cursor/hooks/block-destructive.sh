#!/usr/bin/env bash
# Sample hook: ask the user before any shell command that looks destructive.
#
# Wired in .cursor/hooks.json under "beforeShellExecution".
# Input arrives on stdin as JSON: { "command": "...", "cwd": "...", ... }
# Output is JSON on stdout: { "permission": "allow" | "deny" | "ask", ... }
#
# Exit code 0 = success. Exit code 2 = block. Other non-zero = fail open
# unless failClosed:true is set in hooks.json.

set -euo pipefail

input=$(cat)

# jq is the only external dependency. If it is missing, fail open so the
# starter repo still works for trainees who have not installed it yet.
if ! command -v jq >/dev/null 2>&1; then
  echo '{ "permission": "allow" }'
  exit 0
fi

command=$(echo "$input" | jq -r '.command // empty')

destructive_pattern='rm -rf|git push --force|git reset --hard|drop database|drop table|kubectl delete|terraform destroy'

if [[ "$command" =~ $destructive_pattern ]]; then
  cat <<EOF
{
  "permission": "ask",
  "user_message": "This command looks destructive. Review it before continuing.",
  "agent_message": "A repository hook flagged this command. Confirm with the user before retrying."
}
EOF
  exit 0
fi

echo '{ "permission": "allow" }'
exit 0
