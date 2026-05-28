# 11 — Documentation and runbooks

> Trust boundary: knowledge that survives the people who built the system. If a single engineer leaving creates a continuity risk, the docs are not production-ready.

## Source of truth

- Ingka IIDA Engineering Framework (Confluence `IIDA/970860277`): "Up-to-date README is in place… **MKdocs preferred for in-repo docs that need broader visibility.** Architecture Decision Records (ADRs) used. Inline docstrings for public functions."
- IIDP skill: [`iidp-documentation-standards`](../../skills/iidp-documentation-standards/SKILL.md) — Python docstrings, TypeScript JSDoc, README structure.
- Google SRE — "Production Readiness Review" emphasises operational runbooks tied to alerts.

## Minimum README

Every IIDP repo's `README.md` answers, in this order:

1. **What** — one paragraph on what the system does.
2. **Who** — owners, on-call group, Jira project, link to Confluence space.
3. **Run locally** — exact commands. Must work on a fresh checkout with `make dev` or equivalent.
4. **Test** — `pytest`, `npm test`, coverage threshold.
5. **Deploy** — branch/tag rules, how Dev and Prod deploys are triggered (refer to [06](06-ci-cd.md)).
6. **Environments** — URL per env, secret scope name, monitoring dashboard link, log query.
7. **Architecture** — embed or link to the C4 diagram (see ADRs below).
8. **Contributing** — branch naming, Conventional Commits, PR review expectations.

Anti-patterns:

- README that talks about the framework (FastAPI, React) more than the product.
- README that goes out of date by sprint two — no owner for it, no "doc lint" in CI.
- "See Confluence" for everything — leaves new joiners blocked at access-request stage.

## Architecture Decision Records (ADRs)

ADRs live under `docs/adr/` as `NNNN-<topic>.md`. One ADR per significant decision (database choice, auth model, deployment topology, vendor selection, breaking refactor).

Template:

```markdown
# ADR-0001: <decision>

- Status: Proposed | Accepted | Superseded by ADR-NNNN
- Date: YYYY-MM-DD
- Deciders: <names + roles>
- Consulted: <names>

## Context

What problem are we solving? What constraints apply (tenant policies, time, budget,
existing systems)? Reference the maturity / WAF axes affected.

## Decision

The single sentence that captures what we will do.

## Consequences

- Positive: …
- Negative: …
- Operational: alerts, runbooks, migration steps that this decision creates.

## Alternatives considered

- Option A — rejected because …
- Option B — rejected because …
```

ADR rules:

- Numbered sequentially, never reused.
- Status `Accepted` is set in the PR that ships the change, not before.
- Superseding ADRs link both ways.
- ADR-0001 is reserved for "we use ADRs"; the format above is ADR-0001 itself.

## Runbooks

Runbooks live under `docs/runbooks/` and are referenced by name from alerts and dashboards. One runbook per recurring failure pattern.

| Runbook | Trigger | Owner |
|---|---|---|
| `incident-response.md` | Any P1/P2 alert | On-call |
| `rollback.md` | Failed prod deploy or post-deploy regression | Deploy lead |
| `migration-failure.md` | Alembic step failed mid-deploy | DBA lead |
| `secret-rotation.md` | Rotation due, or compromise suspected | Security |
| `kv-recovery.md` | Accidental secret delete | Security |
| `lakebase-outage.md` | Postgres unavailable | Platform |
| `databricks-job-failure.md` | Job alert fired | Data-eng on-call |
| `app-restart.md` | App Service degraded | On-call |

Runbook content (template):

```markdown
# Runbook: <symptom>

## Detection
- Alert: <name + link to alert rule>
- Symptom: <user-visible behaviour>
- Log query (LAW):
  ```kql
  AppExceptions | where TimeGenerated > ago(15m) | …
  ```

## Diagnosis (5–10 minutes max)
1. Check `<dashboard link>` for …
2. If `<X>` then go to step A; if `<Y>` then step B.

## Mitigation
- Step-by-step. Each step has a single command or a UI path. No "tribal knowledge".
- Time-to-mitigate estimate.

## Resolution
- The fix. Always link the PR or commit.

## Communication
- Who to notify (DL, Teams channel).
- Status-page update template.

## Post-incident
- Open a P-EVENT Jira; tag the incident commander.
- Schedule the blameless review.
```

## OpenAPI specification

FastAPI emits an OpenAPI document at `/openapi.json`. Required hygiene:

- Every route has a `summary`, `description`, `tags`, response model, and (where 4xx is expected) explicit `responses` with error schemas.
- The doc is exported as `docs/openapi.json` on every release tag and uploaded as a release artifact.
- The frontend's API client is generated from this spec (OpenAPI Generator / `openapi-typescript`) — no hand-written types.
- `/docs` and `/redoc` disabled in prd unless the API is intentionally public.

## Docstrings

Python — Google style:

```python
def get_user_by_email(email: str, session: Session) -> User | None:
    """Look up a user by primary email.

    Args:
        email: RFC 5322 primary address. Case-insensitive.
        session: Open SQLAlchemy session.

    Returns:
        The matching User row, or None when no row matches.

    Raises:
        ValueError: If `email` is empty or whitespace-only.
    """
```

TypeScript — JSDoc on exported types and functions:

```ts
/**
 * Build the URL for fetching the bimonthly review for a given org unit.
 *
 * @param orgCode - Org unit identifier (3-letter code).
 * @param period - Bimonthly period in `YYYY-PNN` format.
 * @returns Absolute URL pointing at the FastAPI backend.
 */
export function reviewUrl(orgCode: string, period: string): string { ... }
```

The IIDP `iidp-documentation-standards` skill is the full reference.

## MKdocs (per IIDA framework)

When a repo's docs grow past a single README:

- Add `mkdocs.yml` + `docs/`.
- Build the site in CI; publish to GitHub Pages (private) or a Confluence page.
- Front matter and structure consistent across IIDP repos so cross-linking is predictable.

## Comments — why, not what

Per the IIDP non-negotiables: code is self-documenting; comments explain reasoning, trade-offs, constraints. Anti-patterns: `// increment counter`, `# this is the user id`. Allowed: `// retry budget intentionally exhausted to surface the upstream outage`.

## Common gaps to flag

| Severity | Finding | Fix |
|---|---|---|
| Blocker | No `README.md`, or README cannot get a new developer running locally. | Restore the minimum 8 sections. |
| Blocker | No runbook on a P1 alert. | Add the runbook; link it from the alert rule. |
| Blocker | OpenAPI docs route public in prd without auth. | Disable `/docs` in prd or gate behind auth. |
| High | No ADRs for major decisions (auth model, deployment topology). | Write the missing ADRs retroactively. |
| High | Docstrings missing on public functions. | Add Google-style for Python, JSDoc for TS. |
| High | README references env vars that no longer exist. | Update or remove. |
| High | Runbooks not referenced from alerts. | Add `<runbook-url>` to alert annotations. |
| Medium | OpenAPI doc not exported on release. | Add the export step to the release workflow. |
| Medium | Frontend API client hand-written rather than generated. | Switch to OpenAPI Generator. |
| Medium | ADRs without status, or status `Proposed` for >1 sprint. | Decide or close. |
| Low | Comments that paraphrase the code. | Delete. |
| Info | Repo would benefit from MKdocs but has none. | Add when README outgrows itself. |

## What to grep for in a PR

```bash
test -f README.md && wc -l README.md                       # exists, has content
rg -n '^# Runbook' docs/runbooks/ -g '*.md'                 # any runbooks?
rg -n '^# ADR-' docs/adr/ -g '*.md'                         # any ADRs?
rg -n 'NotImplementedError|TODO\|FIXME' --type py --type ts # unmet promises
rg -n '/docs|/redoc' app/main.py app/backend/main.py        # OpenAPI exposure
```

## Maturity rubric (1–4)

| Score | Description |
|---|---|
| 1 | README is a stub. No ADRs. No runbooks. Knowledge lives in Slack/Teams. |
| 2 | README runs locally. One or two runbooks. Some docstrings. |
| 3 | README covers all 8 sections, ADRs for major decisions, runbook per P1 alert, OpenAPI auto-published, docstrings on public surface. |
| 4 | Above, plus MKdocs site, frontend API client generated, doc-lint in CI, quarterly doc-rot sweep, ADRs reviewed at architecture forum. |

## Cross-references

- [06-ci-cd.md](06-ci-cd.md) — release artefact export.
- [07-observability.md](07-observability.md) — alerts referencing runbooks.
- [08-alembic-migrations.md](08-alembic-migrations.md) — rollback runbook content.
- [`iidp-documentation-standards`](../../skills/iidp-documentation-standards/SKILL.md).
