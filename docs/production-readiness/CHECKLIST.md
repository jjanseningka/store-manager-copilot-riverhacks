# IIDP PR Checklist

Paste this into the PR description (or use it as a self-review before requesting review). Tick items that apply to the diff. Skip groups that the diff does not touch. Anything marked **Blocker** must be done before merge.

> Linked authoritative docs live in this folder. Click through for the why behind each item.

## Cross-cut (always check)

- [ ] **Blocker** — No hardcoded secret, token, password, connection string, or PII in the diff. ([02-secrets.md](02-secrets.md))
- [ ] **Blocker** — No `--no-verify` reference; pre-commit ran cleanly.
- [ ] No `.env` (production or otherwise) added to the repo. Only `.env.config` (non-secret refs) or `.env.example` are committable.
- [ ] Conventional Commit subject with a Jira key, e.g. `feat(api): add /healthz [IIDA-1234]`. ([06-ci-cd.md](06-ci-cd.md))
- [ ] PR description names the user-visible change and the risk class.
- [ ] CODEOWNERS reviewer assigned; if the PR touches infra or auth, the platform/security CODEOWNER approved.

## Supply chain ([01-supply-chain.md](01-supply-chain.md))

If `pyproject.toml`, `poetry.lock`, `uv.lock`, `package.json`, or `package-lock.json` changed:

- [ ] **Blocker** — Lockfile committed alongside the manifest change. No "I'll lock locally" comments.
- [ ] **Blocker** — Python lockfile has hashes (Poetry: default; uv: `uv lock` keeps SHA-256 entries).
- [ ] New direct dependency justified in PR description (why this package, why this version).
- [ ] No package added with `< 30 days` since first publish unless explicitly justified (release-age cooldown).
- [ ] `pip-audit` / `safety` (Python) and `npm audit --omit=dev` (Node) clean in CI.
- [ ] Frontend `package.json` install uses `npm ci --ignore-scripts` in CI.
- [ ] If JFrog mirror is wired (per tenant policy), the install pulls from JFrog, not public PyPI / public npm.

## Secrets ([02-secrets.md](02-secrets.md))

If anything touches auth, secrets, or env handling:

- [ ] **Blocker** — Gitleaks pre-commit + CI ran clean.
- [ ] **Blocker** — New secret added is in Azure Key Vault, Databricks secret scope, GitHub Encrypted Secret, or 1Password — and referenced by name only in code.
- [ ] **High** — Local-dev pattern follows the three-file layout: `.env.config` (non-secret), `.env.1password` (op refs), `.env.local` (rendered output, git-ignored).
- [ ] Key Vault RBAC role chosen correctly: `Key Vault Secrets User` for reads, `Key Vault Secrets Officer` only for write paths.
- [ ] Service principal / managed identity used; no PAT or long-lived API key.
- [ ] If a secret was rotated, rotation runbook + downstream notification listed in PR.

## FastAPI production ([03-fastapi-production.md](03-fastapi-production.md))

If backend code, `gunicorn.conf*`, or middleware changed:

- [ ] **Blocker** — `/healthz` (liveness) and `/readyz` (readiness, includes DB + dependent services) both exposed.
- [ ] **High** — Gunicorn worker count set: `-w (2 * CPU) + 1` for sync; `-k uvicorn.workers.UvicornWorker` if async; `--preload` only with thread-safe globals.
- [ ] **High** — CORS allowlist explicit (no `allow_origins=["*"]` in prod).
- [ ] Rate limit on auth + write routes (per-IP and per-user).
- [ ] Structured JSON logs; no `print()`; correlation ID propagated.
- [ ] `lifespan` context manages startup/teardown (DB pool, HTTP client, cache); no module-level singletons.
- [ ] Trusted-proxy / forwarded-header config is correct for the deploy target (Databricks Apps strips and re-injects).

## React frontend ([04-react-frontend.md](04-react-frontend.md))

If `frontend/src/**` changed:

- [ ] **High** — Routes lazy-loaded with `React.lazy` + `Suspense`.
- [ ] **High** — No `console.log` in production bundle (build strips them; verify locally).
- [ ] **High** — Initial JS budget under 250 KB gzipped; check `webpack-bundle-analyzer` or equivalent if a vendor lib was added.
- [ ] Lockfile committed; `npm ci` used in CI (never `npm install`).
- [ ] No inline scripts; CSP allows only the required sources.
- [ ] Error boundary on each routed view; user-visible error is non-technical.
- [ ] No `dangerouslySetInnerHTML` unless explicitly sanitised.

## Testing ([05-testing.md](05-testing.md))

If logic changed:

- [ ] **Blocker** — Tests added or extended for the change. Bug-fix PRs include a regression test that fails on `main`.
- [ ] Pytest layout mirrors `src/`; file is `test_<module>.py`.
- [ ] AAA pattern (Arrange / Act / Assert) used; one behaviour per test; descriptive name.
- [ ] Async code uses `pytest-asyncio` with `AsyncMock`.
- [ ] Coverage gate passes: ≥80% line; 100% for business logic; explicit `# pragma: no cover` only where justified.
- [ ] No external network calls in unit tests; all externals mocked.
- [ ] React Testing Library used over Enzyme; assertions on rendered output, not implementation details.

## CI/CD ([06-ci-cd.md](06-ci-cd.md))

If `.github/workflows/**` or `.pre-commit-config.yaml` changed:

- [ ] **Blocker** — Every third-party action SHA-pinned with a `# vX.Y.Z` comment.
- [ ] **Blocker** — `permissions: contents: read` set at workflow level; per-job expansions are minimal.
- [ ] **Blocker** — Prod workflow uses a tag input + `git describe --tags --exact-match HEAD` guard + `concurrency: <group>` lock + `environment: <env>` with approver list.
- [ ] **High** — OIDC used for cloud auth (`id-token: write`); no long-lived `AZURE_CLIENT_SECRET` in prod paths.
- [ ] Required PR checks: `ruff-check`, `ruff-format`, `pyright`, `bandit`, `gitleaks`, `eslint`, `prettier`, `pytest`, `frontend build`.
- [ ] Branch protection on `main`: required reviewers ≥ 1, required checks, dismiss stale approvals, no force-push.
- [ ] Dependabot enabled for `pip`, `npm`, and `github-actions` (so action SHAs auto-bump).

## Observability ([07-observability.md](07-observability.md))

If logging / metrics / health code changed:

- [ ] **High** — Logs are JSON (key=value not free text); include `request_id`, `user_id` (if known), `route`, `status`, `duration_ms`.
- [ ] No PII in logs (email, name, address, financial data) unless explicitly classified and approved.
- [ ] No secrets, tokens, or full request bodies in logs.
- [ ] `/healthz` checks process only; `/readyz` checks downstream dependencies and fails fast.
- [ ] Request-timing middleware in place; slow-request threshold logged at WARNING.
- [ ] Error tracking initialised (Defender for Cloud / App Insights / Sentry — whichever the project uses).

## Alembic ([08-alembic-migrations.md](08-alembic-migrations.md))

If `alembic/versions/**` changed:

- [ ] **Blocker** — Exactly one head (`alembic heads` returns 1). Branched heads from concurrent PRs merged before this one lands.
- [ ] **Blocker** — `downgrade()` is implemented and tested.
- [ ] **High** — ENUM operations use a `DO $$` block (idempotent on re-run).
- [ ] **High** — Migration is expand-then-contract for any column rename or type change; new code can read both old and new schema.
- [ ] Dev/prod schema isolation respected (no cross-env DDL).
- [ ] Rollback runbook updated if the change is destructive.

## Databricks ([09-databricks.md](09-databricks.md))

If `databricks.yml`, `app.yaml`, jobs, secret scopes, or UC grants changed:

- [ ] **Blocker** — `databricks bundle validate -t prd` passes in CI.
- [ ] **Blocker** — `targets:` defines `dev` and `prd` with distinct `run_as` service principals.
- [ ] **High** — Secret scopes are per-environment; no shared dev/prd scope.
- [ ] Required IAM scopes declared in `app.yaml`: `iam.access-control:read`, `serving.serving-endpoints:read`, `vectorsearch.vector-search-endpoints:read` (as needed).
- [ ] App-to-app resource references use bundle variables, not duplicated literals.
- [ ] No PAT in code; OAuth or service-principal auth only.

## Azure infra ([10-azure-infra.md](10-azure-infra.md))

If Terraform / CDKTF / Bicep changed:

- [ ] **Blocker** — `https_traffic_only_enabled = true`, `min_tls_version = "TLS1_2"` on storage; HTTPS-only on App Service.
- [ ] **Blocker** — Key Vault: `rbac_authorization_enabled = true`, `purge_protection_enabled = true`, `soft_delete_retention_days >= 90`, `public_network_access_enabled = false`, `default_action = "Deny"` with `AzureServices` bypass.
- [ ] **High** — Managed identity used over SPN where the resource supports it.
- [ ] **High** — RBAC role assigned at resource scope, not subscription scope (per-resource RBAC pattern).
- [ ] Cost tags present (`env`, `owner`, `cost-centre`, `product`).
- [ ] Diagnostic settings route to LAW + storage; per-resource categories chosen.
- [ ] Defender for Cloud plan enrolment confirmed for the new resource type (tenant-managed; check 12-ingka-shared-services.md).

## Docs + runbooks ([11-docs-runbooks.md](11-docs-runbooks.md))

If the change is user-visible or alters ops behaviour:

- [ ] README updated (overview, quickstart, dev, deploy, ops).
- [ ] MKdocs + Google-style docstrings on new public functions/classes.
- [ ] ADR added for any material design decision.
- [ ] Runbook (incident / rollback / migration failure / secret rotation) updated if the change affects ops.
- [ ] OpenAPI spec regenerated and published if API surface changed.
- [ ] If the change touches an NIS2-relevant control (incident handling, supply chain, cryptography, MFA — see [13-compliance-baselines.md](13-compliance-baselines.md)), note which Article 21 §2 measure is affected.

## Final verdict (PR author + reviewer)

- [ ] All Blocker items satisfied.
- [ ] All High items either satisfied or tracked as follow-up tickets (link them in the PR description).
- [ ] CI is green on the latest commit.
- [ ] Mergeable.
