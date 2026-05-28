# 02 — Secrets

> Trust boundary: who can read, rotate, and revoke each credential. The IIDA framework is explicit: no hardcoded secrets, no secrets in logs, no PII stored or logged. Secrets live in Azure Key Vault, Databricks secret scopes, GitHub Encrypted Secrets, or 1Password.

## Source of truth

- Ingka IIDA Engineering Framework (Confluence `IIDA/970860277`): "No hardcoding of sensitive data or PII are stored or logged. All secrets are stored in a Keyvault or secrets in GitHub. Code scanning is enabled on all repos."
- `ii-dig-iidp-infra/docs/security/01-identity.md`: per-resource RBAC pattern, two-plane SPN model (`AZURE_*` app identity vs `ARM_*` deployer identity), Lakebase OAuth passthrough.
- `ii-dig-iidp-infra/docs/security/03-resources.md`: Key Vault hardening (RBAC enabled, purge protection on, soft-delete 90 days, public access disabled, deny-by-default ACL).
- IIDP skill: [`iidp-local-secrets`](../../skills/iidp-local-secrets/SKILL.md) — local-dev pattern.
- IIDP skill: [`iidp-databricks-app-auth`](../../skills/iidp-databricks-app-auth/SKILL.md) — Databricks App auth model.

## Three-file local-dev layout

Every IIDP repo should support this layout, even if only one of the three files is checked in.

| File | In git? | Purpose |
|---|---|---|
| `.env.config` | Yes | Non-secret config (URLs, region, log level). 1Password secret references go here as placeholders, e.g. `DB_PASSWORD={{ op://Work/db/credential }}`. |
| `.env.1password` | Yes (template only, no real secret references) | Defines which 1Password vault each placeholder resolves from, when this differs by env. |
| `.env.local` | **No** (git-ignored) | Rendered output. Produced by `op inject -i .env.config -o .env.local`. Loaded by the app and by `pytest`. Re-rendered on every secret rotation. |

Python loader pattern (used by IIDP services + MCP servers):

```python
from pathlib import Path
from dotenv import load_dotenv

def load_env() -> None:
    here = Path(__file__).resolve().parent
    for candidate in (here / ".env.local", here / ".env.config"):
        if candidate.exists():
            load_dotenv(candidate, override=True)
```

The `.env.local` file is rendered by `op inject` so it never lives in 1Password's clipboard or in shell history. Direnv (`.envrc`) auto-loads the rendered file on `cd`.

## Production secret backends

| Backend | When to use | Owner / lifecycle |
|---|---|---|
| **Azure Key Vault** | Anything Azure-managed; app secrets consumed by a managed identity. | Allen (SPN provisioning) + Ingka platform. RBAC, not access policies. |
| **Databricks secret scope (KV-backed)** | Anything consumed by a Databricks workspace, job, or App. | IIDP infra repo provisions the scope; workspace MSI reads it. |
| **GitHub Encrypted Secrets / Environments** | CI-time secrets (deploy credentials, JFrog OIDC token). | Repo admin; environment approver list gates prod. |
| **1Password** | Local-dev only; CLI references for `op inject`. | Per-user vaults; team vaults for shared dev keys. |

Never use:

- A `.env` file committed to git (any name).
- A "secret" set inside Databricks workspace UI without a backing KV (workspace secrets bypass tenant audit).
- A Databricks personal access token (PAT) — use OAuth or SPN.
- A long-lived Azure SPN secret in a prod workflow — use OIDC federation.

## Key Vault hardening — required settings

The audit-grade reference in `03-resources.md` confirmed the IIDP estate runs:

| Property | Required value | Defender control |
|---|---|---|
| `rbac_authorization_enabled` | `true` | `55ed2823-...` Healthy |
| `purge_protection_enabled` | `true` | `4ed62ae4-...` Healthy |
| `soft_delete_retention_days` | `90` (Azure default; do not lower) | `78211c00-...` Healthy |
| `public_network_access_enabled` | `false` | `f6b59724-...` (PE) — Healthy when PE is added |
| `network_acls.default_action` | `Deny` | `52f7826a-...` Healthy |
| `network_acls.bypass` | `AzureServices` | (covered by above) |

Per-resource RBAC pattern (do **not** assign at subscription scope):

```terraform
resource "azurerm_role_assignment" "spn_reads_kv" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Secrets User"      # reads only
  principal_id         = data.azurerm_client_config.current.object_id
  principal_type       = "ServicePrincipal"
}
```

When a write path is needed (rotation, app-managed secret), use `Key Vault Secrets Officer` instead — and document why. The IIDP `system_stack.py` uses `Secrets User` in code today but runtime is `Secrets Officer` because the portal writes to KV-backed secret scopes (RISK-20 in `01-identity.md`). Either match the doc to runtime or downgrade runtime; do not drift.

## Databricks secret scopes

- Use KV-backed secret scopes only (`databricks_secret_scope` with `keyvault_metadata`). Workspace-managed scopes bypass tenant audit.
- One scope per environment; never share `dev` and `prd`.
- Workspace MSI reads the underlying KV via the access connector pattern (see `ii-dig-iidp-infra/docs/security/04-data-access.md`).
- Application code reads via `dbutils.secrets.get(scope, key)` or `WorkspaceClient.secrets.get_secret(...)`. Never echo to logs.

## Lakebase identity passthrough

- No static Postgres passwords. Lakebase uses short-lived OAuth tokens issued by Databricks.
- The deployer SPN is the only non-human identity needing DDL access for migrations; access is granted via the `iidp_db_admins` `NOLOGIN` role (per the grant script in `01-identity.md`).
- Token TTL is short (minutes). Apps should refresh per request or use the SDK's auto-refresh handler.

## Gitleaks

Every IIDP repo runs Gitleaks in pre-commit and CI. Example pre-commit config:

```yaml
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.30.0
  hooks:
    - id: gitleaks
      exclude: ^(.*\.template$|.*\.example$|\.secrets\.baseline$)
```

CI duplicates the check so `--no-verify` cannot bypass:

```yaml
- name: Gitleaks
  uses: gitleaks/gitleaks-action@<full-sha> # v2.x
  with:
    config-path: .gitleaks.toml
```

A `.secrets.baseline` (detect-secrets format) is allowed only for confirmed false positives (test fixtures, example payloads). Every entry must have a comment explaining why.

## OIDC federation for cloud access

Replace long-lived secrets where possible:

| Cloud / service | OIDC support | Replaces |
|---|---|---|
| Azure | `azure/login@<sha>` with `client-id` + `tenant-id` + `subscription-id` and `id-token: write` | `AZURE_CLIENT_SECRET` in GitHub secrets |
| JFrog | `jfrog/setup-jfrog-cli@<sha>` with `oidc-provider-name` + `oidc-audience` | Long-lived JFrog token |
| AWS (when applicable) | `aws-actions/configure-aws-credentials@<sha>` | AWS access keys |

Long-lived secrets remain acceptable for:

- Per-tier deployer SPN in the `bootstrap-{env}` GitHub Environment when OIDC federation is not yet wired (RISK-36 in `01-identity.md`). Track as Medium; plan OIDC migration.
- Service-to-service auth where the target does not support OIDC.

## Common gaps to flag

| Severity | Finding | Fix |
|---|---|---|
| Blocker | Secret value in source. | Move to KV / secret scope / 1Password; rotate the leaked value; re-run Gitleaks. |
| Blocker | `.env` (real, not `.env.example`) committed. | Remove from history, rotate every secret in the file, add to `.gitignore`. |
| Blocker | PAT or long-lived API key in workflow. | Switch to OIDC or SPN auth. |
| Blocker | KV `public_network_access_enabled = true` in IaC. | Set to `false`; if remote access is needed, add a PE. |
| Blocker | KV `default_action = "Allow"` or no network ACL. | Set `default_action = "Deny"` with `bypass = ["AzureServices"]`. |
| High | KV `purge_protection_enabled = false`. | Enable. Cannot be undone; consider blast radius. |
| High | KV `soft_delete_retention_days < 90`. | Set to 90 (Azure default). |
| High | Same secret scope shared across dev/prd. | Split into per-env scopes; rotate the shared secrets. |
| High | Role assignment at subscription scope for `Key Vault Secrets Officer`. | Move to per-resource scope unless tenant policy requires otherwise. |
| Medium | `.secrets.baseline` entry with no comment. | Add a one-line justification per entry. |
| Medium | Workspace-managed secret scope (no `keyvault_metadata`). | Migrate to KV-backed. |
| Medium | Gitleaks in pre-commit only (not CI). | Add the CI job. |
| Low | `op inject` not used; secrets written to disk by hand. | Document the `op inject` pattern in the README. |
| Info | OIDC federation possible but not adopted yet. | Track as a non-urgent improvement. |

## What to grep for in a PR

```bash
rg -nE 'PASSWORD|SECRET|TOKEN|API_?KEY|AZURE_CLIENT_SECRET' --type-not env
rg -n 'sk-[A-Za-z0-9]{20,}' --hidden                       # OpenAI keys
rg -n 'AKIA[0-9A-Z]{16}'                                   # AWS access keys
rg -nE 'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.'       # JWT
rg -n 'public_network_access_enabled\s*=\s*true' --type tf
rg -n 'default_action\s*=\s*"Allow"' --type tf
rg -n 'no-verify'                                          # bypass attempt
```

## Maturity rubric (1–4)

| Score | Description |
|---|---|
| 1 | Secrets live in `.env` files in git, or hardcoded. No Gitleaks. No KV. |
| 2 | KV exists but loose ACL. Gitleaks runs but doesn't gate. Some secrets in GitHub variables (plaintext). |
| 3 | KV hardened (RBAC, deny ACL, purge protection, soft-delete 90 days). Gitleaks gates pre-commit + CI. Three-file local layout. KV-backed secret scopes per env. |
| 4 | Above, plus OIDC federation for all CI auth. Per-resource RBAC. Rotation runbook tested. Lakebase OAuth passthrough live. SOC ingests KV diagnostic logs. |

## Cross-references

- [01-supply-chain.md](01-supply-chain.md) — preventing the dependency that exfiltrates secrets.
- [06-ci-cd.md](06-ci-cd.md) — where Gitleaks gates.
- [10-azure-infra.md](10-azure-infra.md) — Key Vault provisioning.
- [14-github-supply-chain.md](14-github-supply-chain.md) — OIDC federation patterns.
- [`iidp-local-secrets`](../../skills/iidp-local-secrets/SKILL.md), [`iidp-databricks-app-auth`](../../skills/iidp-databricks-app-auth/SKILL.md) — IIDP-specific patterns.
