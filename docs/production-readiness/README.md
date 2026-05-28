# Production Readiness — Engineer Reference

Engineer-facing companion to the [`iidp-production-readiness`](../../skills/iidp-production-readiness/SKILL.md) skill. Read this folder when reviewing a PR by hand, preparing a release, onboarding into a new repo, or filling in an audit report.

The skill loads only the capability docs touched by the current task. As a human you can read this index, the [CHECKLIST](CHECKLIST.md), and any one capability doc you need — each is self-contained.

## Two modes

| Mode | Trigger | Output | Audience |
|---|---|---|---|
| **PR review** | "review this PR", "is this diff ready" | A severity-grouped comment block (Blocker / High / Medium / Low / Info) tied to `file:line` | PR author + reviewer |
| **Full audit** | "production readiness", "audit this repo", "is this ready for prod" | A filled-in [ASSESSMENT_TEMPLATE.md](ASSESSMENT_TEMPLATE.md): posture summary, 1–4 capability scores, top-5 risks, remediation backlog | Tech lead, security, platform team |

## Capability map (11 surfaces)

Each capability doc states the controls, the IIDP source of truth, the external authority it maps to, and the common gaps. Read just the capability that matches the change you are reviewing.

| # | Capability | Doc | One-line scope |
|---|---|---|---|
| 01 | Supply chain | [01-supply-chain.md](01-supply-chain.md) | Locked + hashed deps (Poetry/uv), SBOM, npm ignore-scripts, JFrog mirror, SLSA. |
| 02 | Secrets | [02-secrets.md](02-secrets.md) | 1Password, Key Vault, Databricks secret scopes, Gitleaks, no `.env` in git. |
| 03 | FastAPI prod | [03-fastapi-production.md](03-fastapi-production.md) | Gunicorn workers, `lifespan`, CORS, rate limit, healthz/readyz, structured logs. |
| 04 | React frontend | [04-react-frontend.md](04-react-frontend.md) | Lazy routes, tree-shake, no `console.log` in prod, bundle budgets, CSP, `npm ci`. |
| 05 | Testing | [05-testing.md](05-testing.md) | pytest layout, coverage gate, mocked externals, RTL patterns. |
| 06 | CI/CD | [06-ci-cd.md](06-ci-cd.md) | PR gates, branch protection, CODEOWNERS, dev auto / prod tag-gated, Conventional Commits. |
| 07 | Observability | [07-observability.md](07-observability.md) | JSON logs, correlation IDs, healthz/readyz, SLOs, request timing. |
| 08 | Alembic migrations | [08-alembic-migrations.md](08-alembic-migrations.md) | Single head, idempotent ENUM, downgrade, expand-then-contract. |
| 09 | Databricks | [09-databricks.md](09-databricks.md) | Bundle validate, dev/prd targets, `run_as` SPNs, secret scopes per env, IAM scopes. |
| 10 | Azure infra | [10-azure-infra.md](10-azure-infra.md) | HTTPS, KV hardening, managed identities, scoped RBAC, private endpoints, Defender. |
| 11 | Docs + runbooks | [11-docs-runbooks.md](11-docs-runbooks.md) | README structure, ADRs, runbooks, OpenAPI, NIS2 incident timing. |

## Framework + Ingka references

Use these when the user asks "how does this map to X" or when filling in the framework column of an audit.

| # | Reference | Doc |
|---|---|---|
| 12 | Cloud WAF + Google SRE cross-walk | [12-cloud-waf-alignment.md](12-cloud-waf-alignment.md) |
| 13 | CIS Azure v3, NIS2 Art 21, ISO 27001 | [13-compliance-baselines.md](13-compliance-baselines.md) |
| 14 | GitHub supply-chain hardening | [14-github-supply-chain.md](14-github-supply-chain.md) |
| 15 | Ingka engineering baseline (canonical sources) | [15-ingka-engineering-baseline.md](15-ingka-engineering-baseline.md) |

## Authority hierarchy

When two sources disagree, the higher entry wins. The skill always surfaces the conflict explicitly.

1. Ingka tenant policy (Azure Policy, Conditional Access, Defender plans, allowed regions, allowed Actions, JFrog mandate).
2. Ingka IIDA Engineering Framework — [Confluence IIDA/970860277](https://confluence.build.ingka.ikea.com/spaces/IIDA/pages/970860277).
3. `ii-dig-iidp-infra/docs/security/` audit-grade reference (12 chapters mapped to DASF, SBP, SRA, Azure WAF Security pillar, MCSB, CIS Azure v3).
4. External authorities (Azure WAF, AWS WAF, GCP Architecture Framework, Google SRE PRR, CIS Microsoft Azure Foundations v3, NIS2 Art 21, SLSA v1.2, sigstore, JFrog Xray + Curation, Wiz PEACH, GitHub Actions hardening).

## Severity ladder

- **Blocker** — violates a non-negotiable; do not merge.
- **High** — material risk; fix in this PR or open a tracked follow-up before next release.
- **Medium** — real issue, no immediate exposure; ack-and-merge is OK.
- **Low** — style/cleanup; merge regardless.
- **Info** — observation, no action.

## How to update these docs

- Capability docs (01–11) are owned by the IIDP platform team. Add a row, update a control, or extend the "common gaps" section. Keep each file under 500 lines (Cursor Write-tool limit; see [`iidp-write-tool-limits`](../../skills/iidp-write-tool-limits/SKILL.md)).
- Framework docs (12–14) need updating when a new framework version drops (Azure WAF refresh, CIS v4, SLSA v2, etc.). Cite the spec version and date.
- The Ingka baseline doc (15) is updated when the Confluence pages or referenced GitHub repos change materially. The page IDs are stable; the content is not.
- Cite, do not paraphrase. Every claim has either a file path, a Confluence page id, an external URL, or a named framework + control.
- No emojis. Third-person tone. Use `file:line` syntax when referencing code.

## Quick links

- [Skill entry point](../../skills/iidp-production-readiness/SKILL.md)
- [PR checklist (paste into PR description)](CHECKLIST.md)
- [Audit report template](ASSESSMENT_TEMPLATE.md)
- Ingka security architecture (ii-dig-iidp-infra)
