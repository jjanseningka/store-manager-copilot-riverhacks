#!/usr/bin/env pwsh
# Verify the local environment can run the agent scaffold on Windows.
# PowerShell equivalent of bootstrap.sh. Idempotent.
# Run with:  pwsh ./scripts/bootstrap.ps1

$ErrorActionPreference = 'Stop'

$script:ok = 0
$script:warn = 0
$script:fail = 0

function Test-Tool {
  param([string]$Label, [string]$Cmd, [switch]$Optional)

  $found = Get-Command $Cmd -ErrorAction SilentlyContinue
  if ($found) {
    Write-Host "ok   - $Label (${Cmd}: $($found.Source))"
    $script:ok++
    return
  }
  if ($Optional) {
    Write-Host "warn - $Label ($Cmd not on PATH; optional)"
    $script:warn++
  } else {
    Write-Host "miss - $Label ($Cmd not on PATH)"
    $script:fail++
  }
}

Write-Host 'Checking required tools...'
Test-Tool 'Node.js'                          'node'
Test-Tool 'npx (for filesystem MCP)'         'npx'
Test-Tool 'uv (for hello-world MCP)'         'uv'
Test-Tool 'PowerShell 7+'                    'pwsh'

Write-Host ''
Write-Host 'Checking optional tools...'
Test-Tool 'GitHub CLI (for /pr command)'     'gh' -Optional
Test-Tool 'git'                              'git' -Optional
Test-Tool 'pre-commit (local quality gate)'  'pre-commit' -Optional
Test-Tool 'ruff (make lint)'                 'ruff' -Optional
Test-Tool 'pytest (make test)'               'pytest' -Optional
Test-Tool 'pyright (make typecheck)'         'pyright' -Optional

Write-Host ''
Write-Host 'Checking project files...'
if (Test-Path -LiteralPath '.env') {
  Write-Host 'ok   - .env exists'
  $script:ok++
} elseif (Test-Path -LiteralPath '.env.example') {
  Write-Host 'warn - .env missing; copy .env.example and fill in tokens'
  $script:warn++
} else {
  Write-Host 'miss - .env.example missing'
  $script:fail++
}

Write-Host ''
Write-Host 'Running scaffold smoke check...'
& pwsh -NoProfile -File ./scripts/agent-smoke-check.ps1
if ($LASTEXITCODE -eq 0) { $script:ok++ } else { $script:fail++ }

Write-Host ''
if (Get-Command pre-commit -ErrorAction SilentlyContinue) {
  if ((Test-Path '.git') -and -not (Test-Path '.git/hooks/pre-commit')) {
    Write-Host 'Installing pre-commit git hook...'
    & pre-commit install
  } else {
    Write-Host 'ok   - pre-commit git hook already installed (or no .git dir yet)'
  }
} else {
  Write-Host "warn - pre-commit not installed; run 'uv tool install pre-commit' or 'pip install pre-commit'"
}

Write-Host ''
Write-Host "Summary: $($script:ok) ok, $($script:warn) warn, $($script:fail) fail"

if ($script:fail -gt 0) {
  Write-Host ''
  Write-Host 'Next steps:'
  Write-Host "  - Install any 'miss' tools above."
  Write-Host '  - Windows: winget install OpenJS.NodeJS astral-sh.uv Microsoft.PowerShell GitHub.cli'
  exit 1
}

if ($script:warn -gt 0) {
  Write-Host ''
  Write-Host 'Optional tools missing. To install the Python dev toolchain in one shot:'
  Write-Host '  uv tool install ruff'
  Write-Host '  uv tool install pytest'
  Write-Host '  uv tool install pyright'
  Write-Host '  uv tool install pre-commit'
  Write-Host '(Each one is a self-contained install; safe to re-run.)'
}

@'

Bootstrap complete. Next:

  1. Copy-Item .env.example .env  (if you have not yet)
  2. Fill in tokens — see docs/references/mcp-servers.md
  3. Open the repo in Cursor
  4. In Settings -> Hooks, point block-destructive at the .ps1 variant
     (see .cursor/hooks/README.md). The default hooks.json points at
     the .sh variant which only works under Git Bash or WSL.
  5. In a fresh chat, ask: "Read AGENTS.md and tell me what you would do
     to make a small change here."

'@ | Write-Host
