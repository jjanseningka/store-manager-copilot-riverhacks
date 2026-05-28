# 06 — CI/CD

> Trust boundary: how code, configs, and artefacts move from a developer's machine to production. Most supply-chain attacks land here.

## Source of truth

- Ingka IIDA Engineering Framework (Confluence `IIDA/970860277`): "Use **GitHub Actions** for CI/CD workflows. Pre-commit checks. Peer review. Push and pull based triggers towards DTAP. Clear commit messages with reference to Jira tags."
- `ii-dig-iidp-infra/docs/security/06-supply-chain.md` — pre-commit toolbelt, JFrog OIDC pattern, environment protection, prod-tag guard, deployer-SPN bootstrap.
- IIDP skill: [`iidp-pre-commit-quality`](../../skills/iidp-pre-commit-quality/SKILL.md) — Ruff, Pyright, ESLint, Bandit, Gitleaks, Terraform fmt/validate, yamllint.
- See [14-github-supply-chain.md](14-github-supply-chain.md) for the deep dive on action pinning, OIDC, SLSA, and attestations.

## Pre-commit baseline (every IIDP repo)

The reference set, taken from the IIDP infra repo:

```yaml
# .pre-commit-config.yaml
default_language_version:
  python: python3.12

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: mixed-line-ending

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.0
    hooks:
      - id: gitleaks

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.2
    hooks:
      - id: ruff-format
      - id: ruff-check

  - repo: local
    hooks:
      - id: pyright
        name: Pyright type check
        entry: poetry run pyright
        language: system
        types: [python]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.9.3
    hooks:
      - id: bandit
        args: ['-r', '-c', 'pyproject.toml', '--severity-level', 'medium']

  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.105.0
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
```

Pre-commit is bypassable with `--no-verify`. Every hook is duplicated in CI as a required status check so the bypass is caught at PR time.

## PR-time required checks

`.github/workflows/ci.yml` runs on `pull_request`. Required status checks (configured in branch protection):

| Check | Tool | Failure | Bypass |
|---|---|---|---|
| Lint (Python) | Ruff format + Ruff check | Block | No |
| Lint (TS/JS) | ESLint + Prettier | Block | No |
| Types (Python) | Pyright | Block | No |
| Types (TS) | `tsc --noEmit` | Block | No |
| Security (Python) | Bandit medium | Block | Only via `# nosec` with reason |
| Secrets | Gitleaks | Block | Only via `.gitleaks.toml` allowlist |
| SCA (Python) | `pip-audit` or `safety` | Block on HIGH/CRITICAL | Allowlist with comment |
| SCA (Node) | `npm audit --omit=dev` | Block on HIGH/CRITICAL | Allowlist with comment |
| Tests | `pytest --cov` + Jest/Vitest | Block | No |
| Build | `npm run build`, `poetry build`, `databricks bundle validate` | Block | No |
| IaC | `terraform fmt -check`, `terraform validate`, `terraform plan` | Block | No |
| Conventional Commit | `commitizen check` or `commitlint` | Block | No |
| GitHub Dependency Review | `actions/dependency-review-action` | Block on HIGH/CRITICAL | Allowlist |

## Branch protection (for `main`)

- Require pull request reviews before merging (>= 1, >= 2 for sensitive repos).
- Dismiss stale pull request approvals when new commits are pushed.
- Require review from CODEOWNERS.
- Require status checks to pass — list every required check above.
- Require branches to be up to date before merging.
- Require conversation resolution before merging.
- Require signed commits where contributors have GPG/SSH signing.
- Restrict who can push: admins for emergency + CI bots only.
- Do not allow force pushes.
- Do not allow deletions.

Mirror the same set for `release/*` branches if the repo uses them.

## CODEOWNERS

```
# Default — platform team owns anything not otherwise claimed
*                                  @ingka-digital/iidp-platform

# Security-sensitive paths require security reviewer too
/.github/workflows/                @ingka-digital/iidp-platform @ingka-digital/iidp-security
/src/backend/auth.py               @ingka-digital/iidp-platform @ingka-digital/iidp-security
/src/infrastructure/               @ingka-digital/iidp-platform @ingka-digital/iidp-security
/alembic/                          @ingka-digital/iidp-platform

/src/frontend/                     @ingka-digital/iidp-platform
/app/products/sales/               @ingka-digital/sales-data
```

## Conventional Commits + Jira

```
<type>(<scope>): <subject> [IIDA-1234]

Body explains the why. Wrap at 72.

Refs: IIDA-1234
```

Allowed `<type>`: `feat`, `fix`, `chore`, `refactor`, `docs`, `test`, `ci`, `build`, `perf`, `revert`.

Enforced via `commitlint` in CI. Squash-merge from a PR with one tidy subject is preferred over many small commits. The skill [`stingy-ingvar-commit`](../../skills/stingy-ingvar-commit/SKILL.md) covers terse-message generation.

## Deploy pipeline shape

### Dev — auto on `main`

```yaml
# .github/workflows/deploy-dev.yml
name: Deploy to Dev
on:
  push:
    branches: [main]

permissions:
  contents: read
  id-token: write   # OIDC to Azure

concurrency:
  group: dev-deploy
  cancel-in-progress: true

jobs:
  deploy-dev:
    runs-on: ubuntu-latest
    environment: app-dev
    steps:
      - uses: actions/checkout@<full-sha>           # v4.x
      - uses: azure/login@<full-sha>                # v2.x
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
      - run: ./scripts/deploy.sh dev
```

### Prod — tag-gated with approval

```yaml
# .github/workflows/deploy-prod-release.yml
name: Deploy Production from Release
on:
  workflow_dispatch:
    inputs:
      release_tag:
        description: 'Release version to deploy (e.g. v1.0.0).'
        required: true
        type: string

permissions:
  contents: read
  id-token: write

concurrency:
  group: prod-deployment
  cancel-in-progress: false   # never cancel a prod deploy mid-flight

jobs:
  deploy-prod:
    runs-on: ubuntu-latest
    environment: app-prd          # requires environment approver list
    steps:
      - uses: actions/checkout@<full-sha>
        with: { ref: ${{ inputs.release_tag }} }
      - name: Verify tag matches HEAD
        run: |
          actual=$(git describe --tags --exact-match HEAD)
          if [ "$actual" != "${{ inputs.release_tag }}" ]; then
            echo "Tag mismatch: $actual vs ${{ inputs.release_tag }}" >&2
            exit 1
          fi
      - uses: azure/login@<full-sha>
        with:
          client-id: ${{ secrets.PROD_DEPLOYER_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.PROD_SUBSCRIPTION_ID }}
      - run: ./scripts/deploy.sh prd
```

Required properties of the prod workflow:

- `workflow_dispatch` only, not `push`.
- `environment: app-prd` with approver list configured in the GitHub Environment settings.
- `concurrency: cancel-in-progress: false` blocks parallel prod runs.
- Tag must point at the checked-out HEAD (`git describe --tags --exact-match HEAD`).
- Distinct deployer SPN credentials per env (`DEPLOY_CLIENT_ID_PRD`).

## DTAP triggers

| Env | Trigger | Approval |
|---|---|---|
| **D**ev | Auto on `main` push | None |
| **T**est | Auto after dev succeeds, or manual `workflow_dispatch` | None |
| **A**cceptance (UAT) | Manual `workflow_dispatch` | Product owner |
| **P**roduction | Manual `workflow_dispatch` with release tag | Platform + security CODEOWNER |

Not every IIDP repo runs all four; a typical IIDP app has Dev + Prod with UAT inside Dev.

## Common gaps to flag

| Severity | Finding | Fix |
|---|---|---|
| Blocker | Third-party action not SHA-pinned. | Pin to full 40-char SHA with `# vX.Y.Z` comment. |
| Blocker | Prod deploy on `push` (not `workflow_dispatch`). | Switch to manual + tag input. |
| Blocker | No environment approver list on `app-prd`. | Configure in GitHub UI. |
| Blocker | `GITHUB_TOKEN` has default permissions (read/write all). | Set workflow-level `permissions: contents: read`; expand per job. |
| Blocker | Long-lived `AZURE_CLIENT_SECRET` in prod path. | OIDC federation via `azure/login`. |
| High | No `concurrency` lock on prod workflow. | Add `concurrency: { group: prod-deployment, cancel-in-progress: false }`. |
| High | Pre-commit installed but not duplicated in CI. | Add CI jobs for Ruff/Bandit/Gitleaks. |
| High | Branch protection allows force-push or admin bypass. | Tighten in GitHub branch settings. |
| High | No CODEOWNERS, or sensitive paths not covered. | Add per the template above. |
| High | Commit message without Jira key. | Add commitlint job; squash with proper subject. |
| Medium | No GitHub Dependency Review action on PRs. | Add. |
| Medium | Tag-guard check missing on prod workflow. | Add `git describe --tags --exact-match HEAD`. |
| Low | One `permissions: write-all` in a single job. | Scope to the minimum permission. |
| Info | Reusable workflow not used for shared steps. | Consider; artifact attestations come along for free. |

## What to grep for in a PR

```bash
rg -n '@v\d+($|/)|@main\b|@master\b' .github/workflows/   # unpinned actions
rg -n 'permissions:\s*write-all' .github/workflows/        # too-broad token
rg -n 'on:\s*push:' .github/workflows/deploy-prod*         # auto-deploy to prod
rg -n 'AZURE_CLIENT_SECRET' .github/workflows/             # long-lived secret
rg -n 'no-verify' .                                        # bypass attempt
rg -n 'fail-on-error: false' .github/workflows/            # silently-passing
```

## Maturity rubric (1–4)

| Score | Description |
|---|---|
| 1 | No CI or CI runs only build. No pre-commit. Prod deploy is `kubectl apply` from a laptop. |
| 2 | CI runs lint + tests. Pre-commit exists locally. Prod deploy is automated but uncontrolled (no approval, no tag guard). |
| 3 | Full PR gate set (lint, type, test, SAST, SCA, secrets, build, IaC validate). Branch protection on. CODEOWNERS in place. Prod deploy tag-gated + environment approval + concurrency lock. OIDC federation. |
| 4 | Above, plus GitHub Dependency Review gates PRs, SLSA Build Level 3 attestations on every release, Dependabot + Renovate cover all ecosystems including `github-actions`, all CI auth via OIDC (no long-lived secrets), runbooks tied to deploys. |

## Cross-references

- [01-supply-chain.md](01-supply-chain.md) — SCA + cooldown + SBOM.
- [02-secrets.md](02-secrets.md) — Gitleaks + OIDC.
- [14-github-supply-chain.md](14-github-supply-chain.md) — full GitHub hardening incl. SLSA and attestations.
- [`iidp-pre-commit-quality`](../../skills/iidp-pre-commit-quality/SKILL.md).
