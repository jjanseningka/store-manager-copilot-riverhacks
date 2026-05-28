# 10 — Azure infrastructure

> Trust boundary: tenant-managed Azure resources hosting IIDP. The IIDP infra repo already encodes most controls; the reviewer's job is to confirm the application repo matches the platform contract and does not regress it.

## Source of truth

- `ii-dig-iidp-infra/docs/security/index.md` — 12-chapter audit-grade security architecture for the IIDP Azure landing zone. The remaining chapters cited below are the canonical Ingka baseline.
- `01-identity.md` — Entra ID, group-only RBAC, SPN naming, federated credentials, JIT, Lakebase identity passthrough.
- `02-network.md` — hub-and-spoke, private endpoints, no public IP, NSG defaults.
- `03-resources.md` — Key Vault, storage, LAW defaults.
- `03-resources.md`, `appendix-remediation-patches.md` — KV defence in depth.
- `11-tenant-policies.md`, `12-ingka-shared-services.md` — Defender for Cloud, Azure Policy, Sentinel, shared services already in place.

## Identity — group-only RBAC

- Every Azure role assignment is to a group, never to a user, SPN, or MI directly. The exception (`01-identity.md` RISK-01) is the deployer SPN bootstrap, where the SPN needs `User Access Administrator` at subscription scope to create the groups themselves. That assignment is direct by necessity but is auditable.
- Group naming: `grp_iidp_{component}_{role}_{env}` (e.g. `grp_iidp_kv_secrets_user_prd`, `grp_iidp_storage_blob_reader_dev`).
- An IIDP application's runtime identity (App Service MI, Function App MI, Databricks workspace MI, Access Connector MI) is added to the relevant group; the group has the Azure role.
- Lakebase Postgres roles follow the same pattern (`iidp_db_*` `NOLOGIN` groups; OAuth identities inherit).

## SPN naming and lifecycle

- Naming: `iidp-{app}-{purpose}-{env}` (e.g. `iidp-bimonthly-deployer-prd`, `iidp-bimonthly-runtime-prd`).
- Distinct SPNs per role (deployer vs runtime) and per env. Never share.
- Federated credentials only — no client secrets. GitHub OIDC → SPN federated credential mapped to a specific repo and environment (`environment:app-prd`).
- Rotation: federated creds don't rotate (they have no secret). Audit ownership quarterly via Entra `application-owners` review.

## Network — no public IP

Per `02-network.md`:

- All ingress through Front Door / Application Gateway with WAF.
- No `public_network_access_enabled = true` on the data plane (Storage, KV, Postgres, Cosmos, ACR).
- Private endpoints for every PaaS resource that exposes data.
- DNS zones private and linked to the workload VNet.

App-repo regression checks:

- `azurerm_*` resources with `public_network_access_enabled = true` outside the public-by-design list (Front Door, Application Gateway).
- `azurerm_storage_account` without `network_rules { default_action = "Deny" }`.
- `azurerm_postgresql_flexible_server` without `public_network_access_enabled = false`.
- KV without `public_network_access_enabled = false`.

## Key Vault hardening

Reference: `03-resources.md` plus the KV remediation entry in `appendix-remediation-patches.md`.

| Property | Required value | Why |
|---|---|---|
| `soft_delete_retention_days` | >= 90 | Recover after accidental delete. |
| `purge_protection_enabled` | `true` | Block purge during retention. |
| `enable_rbac_authorization` | `true` | Use Azure RBAC, not legacy access policies. |
| `public_network_access_enabled` | `false` | Force private endpoint. |
| `sku_name` | `premium` for prd | HSM-backed keys; required for CMK. |
| Diagnostic settings | All categories to LAW + storage | Audit who read which secret when. |

Application repos should never `azurerm_key_vault_access_policy` — that's the legacy model. Use `azurerm_role_assignment` against the KV-scoped role.

## Managed Identities

- App Service / Container Apps / Function App / Databricks workspace / Access Connector — system-assigned MI by default; user-assigned only when shared by multiple resources with the same RBAC.
- MI is the identity the runtime uses to read KV, write blobs, call other Azure resources. Never falls back to `DefaultAzureCredential` with `AZURE_CLIENT_SECRET` env vars.
- Application code uses `DefaultAzureCredential()` which picks up MI inside Azure and the developer's `az login` locally.

## Cost tagging

Required tags on every resource:

| Tag | Example | Used for |
|---|---|---|
| `iidp:cost-center` | `IIDP-PORTAL` | FinOps allocation |
| `iidp:owner` | `iidp-platform@ingka.com` | Escalation |
| `iidp:env` | `dev` / `tst` / `acc` / `prd` | Policy targeting |
| `iidp:app` | `bimonthly-app` | Per-app cost rollup |
| `iidp:data-classification` | `public` / `internal` / `restricted` | Tenant policies (see 11-tenant-policies.md) |

Tags propagate from resource group to resource where supported. Azure Policy denies resource creation without the required set.

## Defender for Cloud + Azure Policy

Per `12-ingka-shared-services.md`, the tenant already has:

- Defender for Cloud enabled subscription-wide; CSPM baseline.
- Defender for Storage, Defender for App Service, Defender for Container Registry, Defender for Key Vault enabled.
- Azure Policy initiatives (MCSB, ISO 27001, NIS2-related) assigned at MG scope.
- Sentinel as the SIEM with the IIDP LAW connected.

The app repo's job: don't regress. New resources must inherit the right tags and policies; CI should run `az policy state list` after a `terraform apply` to catch new non-compliant resources.

## Diagnostic settings — dual sink

Reference: `03-resources.md`. Every resource has diagnostic settings sending:

- `AuditEvent` / `Audit` category to LAW (real-time queries, alerts).
- All categories to a storage account (long-term retention, forensic).

Terraform pattern (paraphrased):

```hcl
resource "azurerm_monitor_diagnostic_setting" "kv" {
  name                       = "kv-to-law-and-storage"
  target_resource_id         = azurerm_key_vault.this.id
  log_analytics_workspace_id = data.azurerm_log_analytics_workspace.shared.id
  storage_account_id         = data.azurerm_storage_account.audit.id

  enabled_log { category_group = "audit" }
  enabled_log { category_group = "allLogs" }
  metric      { category = "AllMetrics" }
}
```

## HTTPS / TLS

- TLS 1.2 minimum, prefer 1.3, on every ingress and managed resource.
- `min_tls_version = "TLS1_2"` on Storage; `minimum_tls_version = "1.2"` on App Service; `ssl_enforcement_enabled = true` on Postgres.
- HSTS header from the app; redirect HTTP → HTTPS at the LB.

## Common gaps to flag

| Severity | Finding | Fix |
|---|---|---|
| Blocker | `public_network_access_enabled = true` on data-plane resource. | Set false; add private endpoint. |
| Blocker | KV `purge_protection_enabled = false` or `enable_rbac_authorization = false`. | Set both true. |
| Blocker | Role assigned directly to a user/SPN/MI (not a group). | Move to group; assign the group. |
| Blocker | SPN with a client secret in use. | Move to federated credential. |
| Blocker | Storage `default_action = "Allow"`. | Set to "Deny"; add VNet rule / private endpoint. |
| High | KV `soft_delete_retention_days < 90`. | Raise to 90. |
| High | App Service / Function `https_only = false`. | Set true. |
| High | Postgres `public_network_access_enabled = true`. | Set false; private endpoint. |
| High | LAW `retention_in_days = 30` on prd. | Raise to 90. |
| High | Resource missing one of the required tags. | Add. |
| Medium | Diagnostic setting routes to LAW only, no storage. | Add dual sink. |
| Medium | `azurerm_key_vault_access_policy` (legacy). | Migrate to RBAC. |
| Low | `min_tls_version` not set on App Service. | Set `"1.2"`. |
| Info | Resource not covered by an `azurerm_monitor_diagnostic_setting`. | Add one. |

## What to grep for in a PR

```bash
rg -n 'public_network_access_enabled\s*=\s*true' --type tf
rg -n 'default_action\s*=\s*"Allow"' --type tf
rg -n 'azurerm_key_vault_access_policy' --type tf
rg -n 'purge_protection_enabled\s*=\s*false' --type tf
rg -n 'min(imum)?_tls_version\s*=\s*"1\.0"|"1\.1"' --type tf
rg -n 'client_secret' --type tf                          # any SPN secret?
rg -n 'tags\s*=\s*\{\s*\}' --type tf                     # empty tag block
```

## Maturity rubric (1–4)

| Score | Description |
|---|---|
| 1 | Resources created via the portal. Public IPs everywhere. KV with access policies. User-direct role assignments. |
| 2 | Terraform exists. Some private endpoints. Mix of MI and SPN-with-secret. Diagnostic settings inconsistent. |
| 3 | Group-only RBAC. Federated SPN. KV hardened (soft-delete >= 90, purge protection, RBAC, private endpoint, premium for prd). All data-plane private. Dual-sink diagnostic settings. Required tags enforced by policy. |
| 4 | Above, plus CMK in KV, Defender plans tuned per service, Policy compliance gated in PR, cost dashboards per app, blameless monthly tenant-posture review. |

## Cross-references

- `ii-dig-iidp-infra/docs/security/01-identity.md`, `02-network.md`, `03-resources.md`, `07-threat-model.md`, `11-tenant-policies.md`, `12-ingka-shared-services.md`, `appendix-remediation-patches.md`.
- [02-secrets.md](02-secrets.md), [12-cloud-waf-alignment.md](12-cloud-waf-alignment.md), [13-compliance-baselines.md](13-compliance-baselines.md).
