#!/usr/bin/env pwsh
# Refresh the workspace lockfile, advancing exclude-newer in the root
# pyproject.toml to "today minus 7 days" (UTC). PowerShell equivalent of
# refresh-lockfile.sh. Run with:
#   pwsh ./scripts/refresh-lockfile.ps1

$ErrorActionPreference = 'Stop'

Set-Location (Join-Path $PSScriptRoot '..')

$pyproject = 'pyproject.toml'

if (-not (Test-Path -LiteralPath $pyproject)) {
  Write-Error "$pyproject not found (expected workspace root)"
  exit 1
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Error "uv not on PATH. Install via 'winget install astral-sh.uv'."
  exit 1
}

$cutoff = (Get-Date).ToUniversalTime().AddDays(-7).ToString('yyyy-MM-ddT00:00:00Z')

Write-Host "Setting exclude-newer to: $cutoff"

$content = Get-Content -LiteralPath $pyproject -Raw
$content = [regex]::Replace(
  $content,
  '(?m)^exclude-newer = .*$',
  ('exclude-newer = "{0}"' -f $cutoff)
)
Set-Content -LiteralPath $pyproject -Value $content -NoNewline

Write-Host "Re-locking workspace ..."
& uv lock

@"

Done. Review the changes with:

  git diff -- pyproject.toml uv.lock

Then commit if the diff looks sane.

"@ | Write-Host
