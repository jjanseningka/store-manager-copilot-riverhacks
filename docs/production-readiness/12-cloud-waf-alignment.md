# 12 — Cloud Well-Architected Framework alignment

> Trust boundary: how IIDP's production-readiness controls map to the cloud vendor frameworks the platform actually deploys against. This file is reference material — the agent reads it when an auditor or architect asks "where does this map in Azure WAF?" or "what does AWS WAR say about this?"

## Source of truth

- Microsoft Azure Well-Architected Framework — five pillars: Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency. Microsoft Cloud Security Benchmark (MCSB) defines the security control set referenced inside the Security pillar.
- AWS Well-Architected Framework — six pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability.
- Google Cloud Architecture Framework — six pillars: Operational Excellence, Security/Privacy/Compliance, Reliability, Cost Optimization, Performance Optimization, AI & ML perspective.
- Google SRE — Production Readiness Review (PRR) checklist as an operational complement to the WAFs.
- Databricks Security and Trust Center — Databricks platform mapping; aligned with MCSB for Azure customers.
- Microsoft Defender for Cloud — runtime detector for many MCSB controls.

The IIDP platform is Azure-hosted. Azure WAF + MCSB is the primary alignment; the other frameworks are cross-references.

## Azure WAF mapping (primary)

| Capability (this folder) | Azure WAF pillar | Representative WAF / MCSB controls |
|---|---|---|
| [01-supply-chain.md](01-supply-chain.md) | Security | SE:02 Secure development lifecycle; SE:03 Threat-modelled supply chain. MCSB DS-6, PV-2. |
| [02-secrets.md](02-secrets.md) | Security | SE:09 Application secrets. MCSB IM-8, IM-9, DS-8. |
| [03-fastapi-production.md](03-fastapi-production.md) | Reliability, Performance | RE:05 Resilient design; PE:07 Code optimization; OE:08 Emergency response. |
| [04-react-frontend.md](04-react-frontend.md) | Security, Performance | SE:08 Hardening; PE:02 Performance plan. |
| [05-testing.md](05-testing.md) | Operational Excellence | OE:06 Workload development; OE:11 Safe deployment practices. |
| [06-ci-cd.md](06-ci-cd.md) | Operational Excellence | OE:03 Software development practices; OE:11 Safe deployment; SE:02. |
| [07-observability.md](07-observability.md) | Operational Excellence, Reliability | OE:07 Workload monitoring; RE:10 Health monitoring; RE:09 Disaster recovery. |
| [08-alembic-migrations.md](08-alembic-migrations.md) | Reliability, OE | RE:08 Test for reliability; OE:11. |
| [09-databricks.md](09-databricks.md) | Security, Reliability | SE:05 Identity and access; DASF mapping for Databricks platform. |
| [10-azure-infra.md](10-azure-infra.md) | Security, Cost, Reliability | SE:01 Security baseline; CO:03 Cost data and reporting; RE:06 Self-preservation. MCSB IM, NS, DP, LT, DS, PV, IR, GS, ES, AM. |
| [11-docs-runbooks.md](11-docs-runbooks.md) | Operational Excellence | OE:02 Operations team formation; OE:08 Emergency response. |

### MCSB control families (cross-cutting)

| MCSB family | Where it lands in IIDP |
|---|---|
| Identity Management (IM) | `01-identity.md`, [02-secrets.md](02-secrets.md), [10-azure-infra.md](10-azure-infra.md). |
| Network Security (NS) | `02-network.md`, [10-azure-infra.md](10-azure-infra.md). |
| Data Protection (DP) | [02-secrets.md](02-secrets.md), [10-azure-infra.md](10-azure-infra.md), `03-resources.md`, `appendix-remediation-patches.md`. |
| Logging & Threat Detection (LT) | [07-observability.md](07-observability.md), [10-azure-infra.md](10-azure-infra.md). |
| DevOps Security (DS) | [01-supply-chain.md](01-supply-chain.md), [06-ci-cd.md](06-ci-cd.md), [14-github-supply-chain.md](14-github-supply-chain.md). |
| Posture & Vulnerability (PV) | [01-supply-chain.md](01-supply-chain.md), [06-ci-cd.md](06-ci-cd.md). |
| Incident Response (IR) | [07-observability.md](07-observability.md), [11-docs-runbooks.md](11-docs-runbooks.md). |
| Governance & Strategy (GS) | This file; [README.md](README.md); `11-tenant-policies.md`. |
| Endpoint Security (ES) | Workstation hardening — out of scope for app repos; covered by Ingka tenant policy. |
| Asset Management (AM) | Tagging in [10-azure-infra.md](10-azure-infra.md). |
| Backup & Recovery (BR) | [08-alembic-migrations.md](08-alembic-migrations.md), runbooks in [11-docs-runbooks.md](11-docs-runbooks.md). |

## AWS WAR cross-reference

For IIDP workloads with AWS components (rare, but possible for partner integrations):

| AWS WAR pillar | Equivalent IIDP capability |
|---|---|
| Operational Excellence (OPS) | [06-ci-cd.md](06-ci-cd.md), [07-observability.md](07-observability.md), [11-docs-runbooks.md](11-docs-runbooks.md). |
| Security (SEC) | [01-supply-chain.md](01-supply-chain.md), [02-secrets.md](02-secrets.md), [10-azure-infra.md](10-azure-infra.md) (translate to IAM, KMS, VPC). |
| Reliability (REL) | [03-fastapi-production.md](03-fastapi-production.md), [08-alembic-migrations.md](08-alembic-migrations.md), [07-observability.md](07-observability.md). |
| Performance Efficiency (PERF) | [03-fastapi-production.md](03-fastapi-production.md), [04-react-frontend.md](04-react-frontend.md). |
| Cost Optimization (COST) | [10-azure-infra.md](10-azure-infra.md) cost tagging; FinOps dashboards. |
| Sustainability (SUS) | Right-size compute, scheduled shutdown on dev resources. |

The agent uses AWS terminology only when reviewing AWS-hosted code; the Azure mapping is canonical for IIDP.

## GCP Cloud Architecture Framework cross-reference

For partner integrations or comparative architecture conversations:

| GCP pillar | Equivalent IIDP capability |
|---|---|
| Operational Excellence | [06-ci-cd.md](06-ci-cd.md), [11-docs-runbooks.md](11-docs-runbooks.md). |
| Security, Privacy, Compliance | [02-secrets.md](02-secrets.md), [10-azure-infra.md](10-azure-infra.md), [13-compliance-baselines.md](13-compliance-baselines.md). |
| Reliability | [03-fastapi-production.md](03-fastapi-production.md), [07-observability.md](07-observability.md). |
| Cost Optimization | Cost tagging in [10-azure-infra.md](10-azure-infra.md). |
| Performance Optimization | [04-react-frontend.md](04-react-frontend.md). |
| AI & ML perspective | Future cross-link to [`databricks-mlflow-evaluation`](../../skills/vendor/ai-dev-kit/databricks-skills/databricks-mlflow-evaluation/SKILL.md) when IIDP ships GenAI features. |

## Google SRE PRR cross-reference

The PRR is operational rather than architectural; it asks "is this safe to launch?" Categories:

| PRR category | IIDP doc |
|---|---|
| Architecture | [10-azure-infra.md](10-azure-infra.md), ADRs in [11-docs-runbooks.md](11-docs-runbooks.md). |
| Capacity planning | [07-observability.md](07-observability.md), SLOs. |
| Change management | [06-ci-cd.md](06-ci-cd.md), [08-alembic-migrations.md](08-alembic-migrations.md). |
| Configuration management | Bundles / Terraform — [09-databricks.md](09-databricks.md), [10-azure-infra.md](10-azure-infra.md). |
| Dependencies | [01-supply-chain.md](01-supply-chain.md). |
| Emergency response | [11-docs-runbooks.md](11-docs-runbooks.md), [07-observability.md](07-observability.md) (alerts → runbooks). |
| Launch coordination | [06-ci-cd.md](06-ci-cd.md) tag-gated prod release. |
| Performance | [03-fastapi-production.md](03-fastapi-production.md), [04-react-frontend.md](04-react-frontend.md). |
| Security | [01-supply-chain.md](01-supply-chain.md), [02-secrets.md](02-secrets.md), [10-azure-infra.md](10-azure-infra.md). |
| Service deployment | [06-ci-cd.md](06-ci-cd.md), [09-databricks.md](09-databricks.md). |

## How to use this file

- In audit mode: copy the relevant rows from the tables above into the "Framework alignment" section of [`ASSESSMENT_TEMPLATE.md`](ASSESSMENT_TEMPLATE.md), then mark which controls are met / partial / gap.
- In PR mode: this file is reference only; the actual checks live in the other capability docs.
- For an auditor's question ("show me MCSB coverage"): start from the MCSB table here, follow each link, harvest the specific control evidence from the capability doc.

## Cross-references

- All capability docs 01-11.
- [13-compliance-baselines.md](13-compliance-baselines.md) — CIS, NIS2, ISO 27001 mapping (different from WAF; compliance vs architectural).
- [14-github-supply-chain.md](14-github-supply-chain.md) — GitHub-specific controls referenced by MCSB DS-6.
