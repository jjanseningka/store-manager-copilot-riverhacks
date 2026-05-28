# 15 — Ingka engineering baseline

> Trust boundary: the existing Ingka / IIDA platform contract. The skill must align with it, not replace it. This file is the cross-walk between the production-readiness checklist in this folder and the canonical Ingka sources.

## Source of truth

- Confluence: **Engineering Framework** (IIDA / `970860277`) — high-level engineering expectations.
- Confluence: **Development Practices** (IIDA / `931372655`) — concrete patterns.
- `ii-dig-iidp-infra/docs/security/` — 12-chapter audit-grade security architecture, the canonical infra baseline.
- IIDP skill library at [`skills/`](../../skills/) — the IIDP "how we do X" knowledge base.

The "**Engineering Framework**" Confluence page (excerpt, paraphrased from the original):

- **Language and tooling**: Python with Poetry. Linting and formatting via Ruff. Type checking via Pyright. Testing via pytest. CI/CD via GitHub Actions. Pre-commit checks on every commit. Secrets in Azure Key Vault.
- **Process**: Peer review on every change. Push and pull-based triggers towards DTAP. Clear commit messages with Jira tag references (Conventional Commits + `[IIDA-NNNN]`).
- **Documentation**: Up-to-date README in every repo. MKdocs preferred for repos with broader-visibility docs. ADRs used. Inline docstrings for public functions.
- **Observability**: Monitoring and alerting rules in place. Error logs in place; able to distinguish infra logs from pipeline logs. **Use logging, not prints.**
- **Performance**: Best practices for Delta / Spark on Databricks (e.g. avoid many small files).
- **Security**: No hardcoded secrets. No PII stored or logged.

## Mapping the framework to this folder

| Engineering Framework item | This folder's coverage |
|---|---|
| Poetry (with uv as accepted alternative) | [01-supply-chain.md](01-supply-chain.md) |
| Ruff, Pyright | [06-ci-cd.md](06-ci-cd.md) pre-commit baseline; [`iidp-pre-commit-quality`](../../skills/iidp-pre-commit-quality/SKILL.md) |
| pytest | [05-testing.md](05-testing.md) |
| GitHub Actions | [06-ci-cd.md](06-ci-cd.md), [14-github-supply-chain.md](14-github-supply-chain.md) |
| Pre-commit | [06-ci-cd.md](06-ci-cd.md) |
| DTAP triggers | [06-ci-cd.md](06-ci-cd.md) deploy pipeline shape |
| Azure Key Vault for secrets | [02-secrets.md](02-secrets.md), [10-azure-infra.md](10-azure-infra.md) |
| Conventional Commits + Jira | [06-ci-cd.md](06-ci-cd.md) |
| Peer review | [06-ci-cd.md](06-ci-cd.md) branch protection + CODEOWNERS |
| README + ADRs + MKdocs + docstrings | [11-docs-runbooks.md](11-docs-runbooks.md) |
| Monitoring + alerting + logs distinguishable | [07-observability.md](07-observability.md) |
| Logging, not prints | [07-observability.md](07-observability.md) |
| Avoid small Delta files | [09-databricks.md](09-databricks.md) |
| No hardcoded secrets, no PII | [02-secrets.md](02-secrets.md), [07-observability.md](07-observability.md) |

If a Confluence update introduces a new mandatory practice, it lands in the relevant capability doc, plus an entry in this table.

## Mapping the infra security architecture

| Infra chapter | This folder's coverage |
|---|---|
| `01-identity.md` (Entra, group-only RBAC, SPN federation, Lakebase identity passthrough) | [02-secrets.md](02-secrets.md), [09-databricks.md](09-databricks.md), [10-azure-infra.md](10-azure-infra.md) |
| `02-network.md` (hub-and-spoke, private endpoints, no public IP) | [10-azure-infra.md](10-azure-infra.md) |
| `03-resources.md` (KV, storage, LAW defaults) | [02-secrets.md](02-secrets.md), [07-observability.md](07-observability.md), [10-azure-infra.md](10-azure-infra.md) |
| `04-data-access.md` (Access Connector pattern, UC grants, FGAC) | [09-databricks.md](09-databricks.md), [10-azure-infra.md](10-azure-infra.md) |
| `05-compute.md` (Databricks workspaces, scopes, system tables) | [09-databricks.md](09-databricks.md) |
| `06-supply-chain.md` (pre-commit, JFrog OIDC, environment protection, prod-tag guard) | [01-supply-chain.md](01-supply-chain.md), [06-ci-cd.md](06-ci-cd.md), [14-github-supply-chain.md](14-github-supply-chain.md) |
| `07-threat-model.md`, `08-risk-register.md` (threat model + tracked risks) | [01-supply-chain.md](01-supply-chain.md), [02-secrets.md](02-secrets.md), [10-azure-infra.md](10-azure-infra.md) |
| `09-references.md`, `10-ms-advisory-crosswalk.md` (CIS, NIS2, ISO, MSRC mapping) | [12-cloud-waf-alignment.md](12-cloud-waf-alignment.md), [13-compliance-baselines.md](13-compliance-baselines.md) |
| `appendix-remediation-patches.md` (KV / storage / network remediation patches) | [02-secrets.md](02-secrets.md), [10-azure-infra.md](10-azure-infra.md) |
| `11-tenant-policies.md` (Azure Policy initiatives) | [10-azure-infra.md](10-azure-infra.md), [13-compliance-baselines.md](13-compliance-baselines.md) |
| `12-ingka-shared-services.md` (Defender for Cloud, Sentinel, log archival) | [07-observability.md](07-observability.md), [10-azure-infra.md](10-azure-infra.md), [13-compliance-baselines.md](13-compliance-baselines.md) |
| `appendix-runtime-validation.md` | Referenced by the audit-mode workflow in [`../../skills/iidp-production-readiness/SKILL.md`](../../skills/iidp-production-readiness/SKILL.md). |

If an infra chapter changes, the corresponding capability doc must be revisited.

## IIDP skill library coverage

The `iidp-production-readiness` skill is the **assessment layer**; the IIDP skill library is the **implementation layer**. The mapping:

| Skill | Assessment doc that references it |
|---|---|
| [`iidp-python-standards`](../../skills/iidp-python-standards/SKILL.md) | [01-supply-chain.md](01-supply-chain.md), [03-fastapi-production.md](03-fastapi-production.md) |
| [`iidp-fastapi-patterns`](../../skills/iidp-fastapi-patterns/SKILL.md) | [03-fastapi-production.md](03-fastapi-production.md) |
| [`iidp-react-typescript-patterns`](../../skills/iidp-react-typescript-patterns/SKILL.md) | [04-react-frontend.md](04-react-frontend.md) |
| [`iidp-skapa-ui-standards`](../../skills/iidp-skapa-ui-standards/SKILL.md) | [04-react-frontend.md](04-react-frontend.md) |
| [`iidp-testing-standards`](../../skills/iidp-testing-standards/SKILL.md) | [05-testing.md](05-testing.md) |
| [`iidp-pre-commit-quality`](../../skills/iidp-pre-commit-quality/SKILL.md) | [06-ci-cd.md](06-ci-cd.md) |
| [`iidp-webpack-build-process`](../../skills/iidp-webpack-build-process/SKILL.md) | [04-react-frontend.md](04-react-frontend.md), [06-ci-cd.md](06-ci-cd.md) |
| [`iidp-performance-debugging`](../../skills/iidp-performance-debugging/SKILL.md) | [03-fastapi-production.md](03-fastapi-production.md), [07-observability.md](07-observability.md) |
| [`iidp-alembic-migrations`](../../skills/iidp-alembic-migrations/SKILL.md) | [08-alembic-migrations.md](08-alembic-migrations.md) |
| [`iidp-databricks-app-auth`](../../skills/iidp-databricks-app-auth/SKILL.md) | [03-fastapi-production.md](03-fastapi-production.md), [09-databricks.md](09-databricks.md) |
| [`iidp-mcp-usage`](../../skills/iidp-mcp-usage/SKILL.md) | Used during audit data-gathering (read JFrog status, KV diagnostic settings via MCP). |
| [`iidp-local-secrets`](../../skills/iidp-local-secrets/SKILL.md) | [02-secrets.md](02-secrets.md) |
| [`devcontainer-1password`](../../skills/devcontainer-1password/SKILL.md) | [02-secrets.md](02-secrets.md) |
| [`iidp-documentation-standards`](../../skills/iidp-documentation-standards/SKILL.md) | [11-docs-runbooks.md](11-docs-runbooks.md) |
| [`iidp-jira-ingka-voice`](../../skills/iidp-jira-ingka-voice/SKILL.md) | Used in audit mode to file Jira follow-ups in the IIDA voice. |
| Databricks vendor skills under `skills/vendor/ai-dev-kit/databricks-skills/` | [09-databricks.md](09-databricks.md) — bundles, app-python, lakebase-provisioned, lakebase-autoscale, mlflow-evaluation, model-serving, vector-search, etc. |

## Authority hierarchy

When two sources disagree, the order of authority is:

1. **Ingka tenant policy** — Azure Policy assignments in the Ingka management group. Non-negotiable; enforced at create-time.
2. **`ii-dig-iidp-infra/docs/security/`** — the audit-grade security architecture. Tenant-aligned; binding for IIDP.
3. **Confluence IIDA Engineering Framework** — Ingka engineering norms for the IIDA org.
4. **`iidp-production-readiness` docs (this folder)** — assessment view onto the above. Cannot weaken (1)-(3); may only narrow / restate / interpret.
5. **External frameworks (Azure WAF, CIS, NIS2, OWASP, SRE)** — used to motivate choices; do not override Ingka decisions.
6. **IIDP skill library** — implementation patterns. Bound by (1)-(4).
7. **Per-repo conventions** — only when not overridden by (1)-(6).

The `iidp-production-readiness` skill cites the higher-authority source in any finding; the citation is the appeal mechanism.

## How to keep this in sync

Quarterly review cycle (calendar item assigned to the platform lead):

1. Diff the Engineering Framework page (Confluence history) against this folder.
2. Diff `ii-dig-iidp-infra/docs/security/` against the relevant capability docs.
3. Diff the IIDP skill library version (`skills/*/SKILL.md`) against the references here.
4. Open one PR per drift; each PR updates only the capability docs and the entry in this file.
5. Announce the change in the IIDA engineering forum.

A failing quarterly review (no drift caught for two consecutive quarters) is itself a finding — likely the platform is stagnating, not stable.

## Cross-references

- [`README.md`](README.md) — entry point.
- [`../../skills/iidp-production-readiness/SKILL.md`](../../skills/iidp-production-readiness/SKILL.md) — agent-facing skill.
- All capability docs 01-14.
