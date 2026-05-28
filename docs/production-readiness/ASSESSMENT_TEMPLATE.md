# Production-Readiness Assessment — `<repo-name>`

> Fill this template in for a full audit. Save the completed report under `docs/agent-output/PROD_READINESS_<DATE>.md` in the target repo. Do not commit until the team has reviewed.

| Field | Value |
|---|---|
| Repo | `<full-path-or-URL>` |
| Audit date | `YYYY-MM-DD` |
| Auditor | `<name or agent + model>` |
| Commit audited | `<sha>` |
| Auditor mode | Production-readiness audit (1–4 maturity) |
| Toolchain | `<Poetry|uv>` · FastAPI `<version>` · React `<version>` · Databricks Bundles · Azure `<CDKTF|Bicep|Terraform>` |
| Deploy target | `<Databricks App | Azure App Service | Kubernetes | ...>` |
| Last validated against | `<framework versions, e.g. Azure WAF March 2026, CIS Azure v3.0, NIS2 Art 21 (2026 enforcement)>` |

## 1. Posture summary (2–4 sentences)

> What is the platform overall, who uses it, what is the blast radius if it fails, and what is the dominant risk class. Cite the README and one or two architectural files.

`<text>`

## 2. Capability scores

Score each capability 1–4 using the rubric below. Quote at least one piece of evidence per score (file path + line, or "absent: searched X, Y, Z and found nothing"). Use the per-capability docs in this folder for the detail.

### Scoring rubric

| Score | Name | Meaning |
|---|---|---|
| 1 | Beginner | Capability is absent or mostly absent. Ad-hoc work, no controls. |
| 2 | Intermediate | Some controls exist; not enforced; gaps in documentation or coverage. |
| 3 | Advanced | Controls in place, enforced in CI, documented; minor gaps acceptable. |
| 4 | Expert | Industry-leading. Controls enforced, audited, measured, and continuously improved. |

### Capability matrix

| # | Capability | Score | Target | Gap | Priority | Evidence + notes |
|---|---|:-:|:-:|:-:|:-:|---|
| 01 | Supply chain | __ | __ | __ | __ | `<file:line / found / absent>` |
| 02 | Secrets | __ | __ | __ | __ | |
| 03 | FastAPI production | __ | __ | __ | __ | |
| 04 | React frontend | __ | __ | __ | __ | |
| 05 | Testing | __ | __ | __ | __ | |
| 06 | CI/CD | __ | __ | __ | __ | |
| 07 | Observability | __ | __ | __ | __ | |
| 08 | Alembic migrations | __ | __ | __ | __ | |
| 09 | Databricks | __ | __ | __ | __ | |
| 10 | Azure infra | __ | __ | __ | __ | |
| 11 | Docs + runbooks | __ | __ | __ | __ | |
| | **Average** | **__** | **__** | | | |

> Priority: H = fix this quarter, M = next quarter, L = nice-to-have.

## 3. Detailed findings per capability

For each capability with a score below the target, write a short section. Two patterns are supported; pick whichever helps the reader.

### Pattern A — narrative

```text
01 Supply chain — score 2 / target 3

What is in place:
- poetry.lock present and hashed.
- Gitleaks runs in pre-commit and CI.

What is missing:
- JFrog mirror not wired; CI installs from public PyPI (RISK-21-equivalent in ii-dig-iidp-infra).
- No SBOM generation step.
- No release-age cooldown in Dependabot config.

Remediation:
- Wire JFrog Artifactory mirror via OIDC; example workflow in 14-github-supply-chain.md.
- Add a CycloneDX SBOM job to the build workflow.
- Add `cooldown: { default-days: 7 }` to .github/dependabot.yml.
```

### Pattern B — control-by-control

```text
01 Supply chain — controls

| Control | Status | Evidence |
|---|---|---|
| Lockfile hashed | OK | poetry.lock |
| Public-PyPI guard | MISSING | .github/workflows/ci.yml:34 |
| SBOM published | MISSING | searched workflows; no cyclonedx step |
```

## 4. Top 5 risks

Rank by combined likelihood and impact. Link each to the capability score and the suggested remediation.

| # | Risk | Likelihood | Impact | Capability | Remediation owner |
|---|---|---|---|---|---|
| 1 | `<risk>` | H/M/L | H/M/L | `<##>` | `<team>` |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

## 5. Prioritised remediation backlog

Group by capability so the team can pick up work in coherent chunks. Each item is one or two lines plus the doc reference.

### This quarter (must fix)

- `<capability>` — `<one-line description>`. Ref: `[<doc>.md](<doc>.md)`.

### Next quarter (should fix)

- `<capability>` — `<one-line description>`. Ref: `[<doc>.md](<doc>.md)`.

### Backlog (track, do not commit dates)

- `<capability>` — `<one-line description>`.

## 6. Framework alignment (optional column)

Fill in only if the user asked for a specific framework. Otherwise skip this section.

| Capability | Azure WAF | AWS WAF | Google SRE PRR | CIS Azure v3 | NIS2 Art 21 §2 |
|---|---|---|---|---|---|
| 01 | SE:02 | Security | Dependencies | 6, 8 | (d), (e) |
| 02 | SE:05, SE:07 | Security | Configuration | 1, 8.5 | (e), (i) |
| ... | | | | | |

> See [12-cloud-waf-alignment.md](12-cloud-waf-alignment.md) and [13-compliance-baselines.md](13-compliance-baselines.md) for the full mapping.

## 7. Ingka authority + tenant assumptions used

State which Ingka assumptions the audit relied on, so a re-audit knows what to re-validate.

- Confluence references consulted: e.g. [IIDA/970860277 Engineering Framework](https://confluence.build.ingka.ikea.com/spaces/IIDA/pages/970860277).
- Repository references consulted: e.g. `ii-dig-iidp-infra/docs/security/03-resources.md`.
- Tenant policies relied on (per `11-tenant-policies.md`): classic-resource ban, region allowlist, Defender plan enrolment, allowed Actions, JFrog mandate.
- Tenant gaps inherited (per the runtime corrections in `01-identity.md` and `03-resources.md`): list any that affect the scored capabilities.

## 8. Re-audit cadence

| Trigger | Action |
|---|---|
| Material change to capabilities 01, 02, 06, 09, 10 | Re-audit those capabilities only. |
| Framework version bump (Azure WAF, CIS, NIS2 enforcement update) | Re-audit sections 2, 6, and refresh [13-compliance-baselines.md](13-compliance-baselines.md). |
| Security incident or near-miss | Full re-audit. |
| Default | Every 6 months. |

## 9. Sign-off

| Role | Name | Date | Notes |
|---|---|---|---|
| Engineering lead | | | |
| Platform / infra owner | | | |
| Security reviewer | | | |
| Product owner | | | |
