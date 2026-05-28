#!/usr/bin/env pwsh
# Sample hook: ask the user before any shell command that looks destructive.
# Windows / PowerShell equivalent of block-destructive.sh. No external
# dependencies (no jq); uses native ConvertFrom-Json / ConvertTo-Json.
#
# Wire by editing .cursor/hooks.json:
#   "command": "pwsh"
#   "args": ["-NoProfile", "-File", ".cursor/hooks/block-destructive.ps1"]
#
# Input arrives on stdin as JSON: { "command": "...", "cwd": "...", ... }
# Output is JSON on stdout: { "permission": "allow" | "deny" | "ask", ... }

$ErrorActionPreference = 'Stop'

$inputJson = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($inputJson)) {
  '{ "permission": "allow" }'
  exit 0
}

try {
  $data = $inputJson | ConvertFrom-Json
} catch {
  # Malformed input -> fail open. Do not block the user on parse errors.
  '{ "permission": "allow" }'
  exit 0
}

$command = [string]$data.command

# Mix of POSIX and PowerShell-flavoured destructive idioms.
$pattern = 'rm -rf|git push --force|git reset --hard|drop database|drop table|kubectl delete|terraform destroy|Remove-Item.*-Recurse.*-Force|rmdir /S|del /F /S'

if ($command -match $pattern) {
  @{
    permission    = 'ask'
    user_message  = 'This command looks destructive. Review it before continuing.'
    agent_message = 'A repository hook flagged this command. Confirm with the user before retrying.'
  } | ConvertTo-Json -Compress
  exit 0
}

@{ permission = 'allow' } | ConvertTo-Json -Compress
exit 0
