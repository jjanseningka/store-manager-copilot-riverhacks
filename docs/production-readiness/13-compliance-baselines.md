# 13 — Compliance baselines

> Trust boundary: external regulations and benchmarks the IIDP platform must satisfy. The infra repo already encodes most of these at tenant scope; the application repo's job is to inherit and not regress.

## Source of truth

- `ii-dig-iidp-infra/docs/security/11-tenant-policies.md` — the Azure Policy initiatives assigned at Ingka management-group scope.
- `ii-dig-iidp-infra/docs/security/12-ingka-shared-services.md` — Defender, Sentinel, log archival.
- CIS Microsoft Azure Foundations Benchmark v2.1 — the canonical Azure hardening reference; Microsoft and Ingka tenant policy track this.
- CIS Critical Security Controls v8 — control families used by Ingka security for IT-wide reporting.
- NIS2 Directive (EU 2022/2555) — applicable to Ingka as an "essential entity" in retail; binding since October 2024.
- ISO/IEC 27001:2022 — Ingka holds a certified ISMS; controls map into Azure Policy initiatives in the tenant.
- OWASP ASVS v5 — application-layer security verification standard.
- OWASP LLM Top 10 — when the workload contains LLM features.
- Databricks AI Security Framework (DASF) — applies to Databricks-resident agents and ML.

This file is reference; the agent reads it when an auditor or security partner asks for an explicit mapping.

## CIS Microsoft Azure Foundations Benchmark v2.1 — IIDP coverage

Selected high-impact controls and where they are enforced in the IIDP repos.

| CIS Azure control | Enforced by | Doc |
|---|---|---|
| 1.1 Ensure that multi-factor authentication is enabled for all non-service accounts. | Ingka tenant (Entra Conditional Access). | `12-ingka-shared-services.md` |
| 1.21 Ensure that no custom subscription owner roles are created. | Group-only RBAC; tenant policy. | [10-azure-infra.md](10-azure-infra.md), `01-identity.md` |
| 2.1 Ensure Defender for Cloud plans are enabled. | Tenant assignment. | [10-azure-infra.md](10-azure-infra.md) |
| 3.1 Ensure that "Secure transfer required" is set on storage accounts. | Terraform default + Policy. | [10-azure-infra.md](10-azure-infra.md) |
| 3.7 Ensure default network access rule for storage accounts is "Deny". | Repo regression check. | [10-azure-infra.md](10-azure-infra.md) |
| 5.1.* Ensure diagnostic settings exist for all subscriptions / resources. | Dual-sink pattern. | [07-observability.md](07-observability.md), [10-azure-infra.md](10-azure-infra.md) |
| 6.1 Ensure Network Watcher is enabled. | Tenant policy. | `02-network.md` |
| 8.1 Ensure soft-delete on Key Vault is enabled. | Repo regression check. | [02-secrets.md](02-secrets.md), [10-azure-infra.md](10-azure-infra.md) |
| 8.2 Ensure purge protection on Key Vault is enabled. | Repo regression check. | [02-secrets.md](02-secrets.md), [10-azure-infra.md](10-azure-infra.md) |
| 9.* App Service controls (TLS, HTTPS only, MI in use). | Repo regression check. | [10-azure-infra.md](10-azure-infra.md) |

The full benchmark is much larger; the table above is the subset most often touched by an application PR.

## CIS Critical Security Controls v8 — IIDP coverage

| CIS Control | Enforced by | Doc |
|---|---|---|
| 1 Inventory and Control of Enterprise Assets | Azure resource inventory + tagging. | [10-azure-infra.md](10-azure-infra.md) |
| 2 Inventory and Control of Software Assets | SBOM on every artefact. | [01-supply-chain.md](01-supply-chain.md), [14-github-supply-chain.md](14-github-supply-chain.md) |
| 3 Data Protection | Encryption at rest (CMK roadmap), in transit (TLS 1.2+). | [02-secrets.md](02-secrets.md), [10-azure-infra.md](10-azure-infra.md) |
| 4 Secure Configuration | Azure Policy, infra-as-code. | [10-azure-infra.md](10-azure-infra.md) |
| 5 Account Management | Entra group-only RBAC; SPN naming. | `01-identity.md` |
| 6 Access Control Management | Conditional Access; PIM. | `01-identity.md` |
| 7 Continuous Vulnerability Management | `pip-audit`, `npm audit`, Defender. | [01-supply-chain.md](01-supply-chain.md), [06-ci-cd.md](06-ci-cd.md) |
| 8 Audit Log Management | LAW + storage dual sink. | [07-observability.md](07-observability.md) |
| 11 Data Recovery | Lakebase backup, Alembic downgrade. | [08-alembic-migrations.md](08-alembic-migrations.md), [11-docs-runbooks.md](11-docs-runbooks.md) |
| 14 Security Awareness | Out of scope for repo PRs. | — |
| 16 Application Software Security | OWASP ASVS subset below. | [03-fastapi-production.md](03-fastapi-production.md), [04-react-frontend.md](04-react-frontend.md), [05-testing.md](05-testing.md) |
| 17 Incident Response | Runbooks + on-call. | [11-docs-runbooks.md](11-docs-runbooks.md) |
| 18 Penetration Testing | External, periodic; out of scope here. | — |

## NIS2 Directive — IIDP coverage

NIS2 Article 21 mandates "appropriate and proportionate technical, operational, and organisational measures" across ten categories. Coverage:

| NIS2 Article 21 category | IIDP coverage |
|---|---|
| (a) Policies on risk analysis and information system security | Ingka ISMS (ISO 27001), Defender for Cloud secure-score. |
| (b) Incident handling | [11-docs-runbooks.md](11-docs-runbooks.md), Sentinel detections per `12-ingka-shared-services.md`. |
| (c) Business continuity and crisis management | Backup policy (Lakebase + storage), rollback runbooks. |
| (d) Supply chain security | [01-supply-chain.md](01-supply-chain.md), [14-github-supply-chain.md](14-github-supply-chain.md), JFrog/Xray. |
| (e) Security in network and information systems acquisition, development, and maintenance | All capability docs 01-11. |
| (f) Policies and procedures to assess the effectiveness | Maturity rubric in this skill; quarterly audits. |
| (g) Basic cyber hygiene practices and training | Out of scope for repo PRs; Ingka HR/Security. |
| (h) Cryptography and encryption | TLS 1.2+, KV-managed keys, CMK roadmap. |
| (i) Human resources security, access control policies, and asset management | Group-only RBAC, tagging. |
| (j) Use of multi-factor authentication | Conditional Access at tenant scope. |

NIS2 incident reporting timelines (24h early warning, 72h notification, 1-month final report) are operational obligations on the Ingka CIRT, not the app team; the app team's contribution is sending high-quality alerts and logs to Sentinel.

## ISO/IEC 27001:2022 — overview

Ingka holds a certified ISMS. From an app-repo perspective:

- Annex A.5 (organisational), A.6 (people), A.7 (physical) — out of scope.
- Annex A.8 (technological) — covered in aggregate by the capability docs 01-11. Notable controls:
  - A.8.2 Privileged access rights — group-only RBAC, `01-identity.md`.
  - A.8.5 Secure authentication — OIDC, MI, no PAT.
  - A.8.8 Vulnerability management — SCA + Defender.
  - A.8.13 Backup — Lakebase + storage redundancy.
  - A.8.24 Cryptography — TLS, KV.
  - A.8.28 Secure coding — every capability doc.

## OWASP ASVS v5 — Level 2 controls

ASVS Level 2 is the baseline for IIDP applications; sensitive data flows target Level 3.

| ASVS chapter | IIDP doc |
|---|---|
| V1 Architecture | ADRs in [11-docs-runbooks.md](11-docs-runbooks.md). |
| V2 Authentication | [`iidp-databricks-app-auth`](../../skills/iidp-databricks-app-auth/SKILL.md), [03-fastapi-production.md](03-fastapi-production.md). |
| V3 Session | Auth via short-lived OAuth tokens; same. |
| V4 Access control | UC grants + FastAPI auth dependencies, [09-databricks.md](09-databricks.md), [03-fastapi-production.md](03-fastapi-production.md). |
| V5 Validation, sanitisation, encoding | Pydantic validation, React-safe HTML, [03-fastapi-production.md](03-fastapi-production.md), [04-react-frontend.md](04-react-frontend.md). |
| V7 Error handling, logging | [07-observability.md](07-observability.md). |
| V8 Data protection | [02-secrets.md](02-secrets.md), [10-azure-infra.md](10-azure-infra.md). |
| V9 Communications | TLS in [10-azure-infra.md](10-azure-infra.md). |
| V10 Malicious code | SBOM + SCA in [01-supply-chain.md](01-supply-chain.md). |
| V11 Business logic | Tests in [05-testing.md](05-testing.md). |
| V12 Files and resources | Resource bounds in [03-fastapi-production.md](03-fastapi-production.md). |
| V14 Configuration | Bundles, Terraform, [09](09-databricks.md), [10](10-azure-infra.md). |

## OWASP LLM Top 10 (for GenAI features only)

When the workload includes LLM features:

| LLM01 Prompt injection | Defence-in-depth; never trust model output in privileged code paths. |
| LLM02 Insecure output handling | Treat LLM output as untrusted; validate. |
| LLM03 Training data poisoning | Curation; lineage via Unity Catalog. |
| LLM06 Sensitive info disclosure | Mask PII before sending to the model; the [`iidp-jira-ingka-voice`](../../skills/iidp-jira-ingka-voice/SKILL.md) pattern. |
| LLM08 Excessive agency | Tool allowlist; least-privilege scopes. |
| LLM10 Model theft | KV-stored API keys for hosted models; logs scrubbed of tokens. |

Apply the [`databricks-mlflow-evaluation`](../../skills/vendor/ai-dev-kit/databricks-skills/databricks-mlflow-evaluation/SKILL.md) and [`databricks-model-serving`](../../skills/vendor/ai-dev-kit/databricks-skills/databricks-model-serving/SKILL.md) skills for the runtime.

## Databricks AI Security Framework (DASF)

DASF maps Databricks platform controls to MITRE ATT&CK for AI workloads. For IIDP:

- Data security (ATT&CK T1530 cloud-stored data exfiltration) — UC FGAC, [09-databricks.md](09-databricks.md).
- Identity and authentication — OAuth / SPN per [09-databricks.md](09-databricks.md).
- Secrets — KV-backed scope per env, [02-secrets.md](02-secrets.md), [09-databricks.md](09-databricks.md).
- Audit — workspace and account logs to LAW via system tables, [07-observability.md](07-observability.md).

## How to use this file

- In an audit: pick the framework the auditor asks about, navigate to the capability doc for evidence.
- Quarterly: review whether new IIDP workloads (especially GenAI) have lifted into NIS2 / DASF scope; update.

## Cross-references

- [10-azure-infra.md](10-azure-infra.md), [12-cloud-waf-alignment.md](12-cloud-waf-alignment.md).
- Tenant-level evidence: `ii-dig-iidp-infra/docs/security/11-tenant-policies.md`, `12-ingka-shared-services.md`.
