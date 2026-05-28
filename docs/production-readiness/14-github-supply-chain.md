# 14 — GitHub supply chain hardening

> Trust boundary: the GitHub organisation itself. A compromised GitHub account, action, or app token defeats every downstream control. This file is the deep dive promised by [06-ci-cd.md](06-ci-cd.md).

## Source of truth

- GitHub's official guidance: "Security hardening for GitHub Actions" and "About supply chain security."
- `ii-dig-iidp-infra/docs/security/06-supply-chain.md` — Ingka's audit-grade chapter; JFrog OIDC, env protection, prod-tag guard.
- SLSA (Supply-chain Levels for Software Artifacts) v1.0 — `slsa.dev`.
- sigstore / cosign — keyless signing model.
- 2024 supply-chain incidents (tj-actions/changed-files compromise; reviewdog action token leak; the npm `ua-parser-js` and `lz-string` events; the `xz-utils` backdoor) — referenced as the threat model.

## Action pinning

Every third-party `uses:` reference pins to a **full 40-character commit SHA**, with the human-readable version in a comment.

```yaml
# Good
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11   # v4.2.2

# Bad — float tag, can be moved by the action owner
- uses: actions/checkout@v4

# Worst — moving branch
- uses: actions/checkout@main
```

First-party (`actions/*`) actions float-by-tag is sometimes acceptable inside a single org workflow when the org has its own trust model. For IIDP, **pin every external action, including `actions/*`**.

Internal actions (same org) may pin to a tag if the org has branch protection on the action repo. Pinning to SHA is still safer.

### Tooling

- `dependabot.yml` with `package-ecosystem: github-actions` — Dependabot opens PRs to upgrade pinned SHAs.
- `ratchet` (CLI) — verifies that every `uses:` is SHA-pinned.
- CodeQL action — runs the standard "Action: not pinned to SHA" rule.

## Workflow permissions — least privilege

Default token permission at the workflow level:

```yaml
permissions:
  contents: read
```

Each job opts up only as needed:

```yaml
jobs:
  release:
    permissions:
      contents: write         # tag + release
      id-token: write         # OIDC to cloud / package registry
      packages: write         # push container to GHCR
      attestations: write     # build provenance attestation
```

Never `permissions: write-all`. Never rely on the org-default token permission; set it explicitly at workflow level.

## OIDC federation

Long-lived secrets (`AZURE_CLIENT_SECRET`, `JFROG_PASSWORD`, `AWS_SECRET_ACCESS_KEY`) are banned in IIDP repos.

Pattern for Azure:

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - uses: azure/login@<full-sha>
    with:
      client-id:       ${{ secrets.AZURE_CLIENT_ID }}      # SPN object ID
      tenant-id:       ${{ secrets.AZURE_TENANT_ID }}
      subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

The SPN's federated credential in Entra is keyed on the GitHub repo and the environment, so a token issued for `org/repo:environment:app-prd` cannot be replayed for any other env.

Pattern for JFrog (per Ingka's infra chapter):

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - name: JFrog OIDC
    uses: jfrog/setup-jfrog-cli@<full-sha>
    with:
      oidc-provider-name: github-iidp
  - run: jfrog rt build-publish
```

No long-lived JFrog identity token in `secrets.JFROG_TOKEN`.

## GitHub Environments

Define environments per deployment target (`app-dev`, `app-tst`, `app-acc`, `app-prd`) and configure:

- **Required reviewers** — at least one for `app-prd`; typically the platform team plus security CODEOWNER.
- **Wait timer** — optional cool-off period before deploy starts.
- **Environment secrets** — scoped to that env only; the GitHub UI shows the env in the secret detail.
- **Deployment branch rule** — `app-prd` accepts deploys only from protected tags matching `v*`.
- **Required deployment status checks** — gate on smoke tests after deploy.

Environments protect the prod credential boundary; they cannot be bypassed by editing `.github/workflows/*.yml` in a feature branch.

## Branch protection

For `main` and `release/*` (mirrors [06-ci-cd.md](06-ci-cd.md)):

- Required PR review (>= 1).
- Dismiss stale approvals on new push.
- Require status checks (the full PR gate set).
- Require linear history (squash merge default).
- No force push, no deletion.
- Signed commits where contributors have GPG/SSH keys configured.
- Restrict who can push: admins and CI bots only.

Tag protection rules:

- Protect `v*` tags. Only the release workflow's identity can create them.

## CODEOWNERS — security-relevant paths

```
# Anything in .github/ requires platform + security
/.github/                          @ingka-digital/iidp-platform @ingka-digital/iidp-security

# Auth code requires security
**/auth.py                         @ingka-digital/iidp-security
**/permissions.py                  @ingka-digital/iidp-security

# Infra requires platform
/infra/                            @ingka-digital/iidp-platform

# DB migrations require DBA
/alembic/                          @ingka-digital/iidp-platform
```

PRs cannot merge unless every covered path has an approval from the listed owner.

## Secret scanning + push protection

GitHub Advanced Security features used:

- **Secret scanning** — historical scan of the repo.
- **Push protection** — blocks pushes that introduce known secret patterns at git push time.
- **Custom patterns** — for Ingka-internal credential formats not covered by the default catalogue.
- **Validity checks** — confirms whether a leaked secret is still live.

Repo-level Gitleaks (per [02-secrets.md](02-secrets.md)) complements push protection for patterns GitHub doesn't ship.

## Dependency Review action

```yaml
- uses: actions/dependency-review-action@<full-sha>
  with:
    fail-on-severity: high
    license-check: true
    allow-licenses: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, MPL-2.0, Python-2.0
```

Fails PRs that introduce new HIGH/CRITICAL vulnerabilities or banned-licence dependencies. Pairs with `pip-audit` / `npm audit` (those run inside CI; Dependency Review reads the diff at GitHub-app level).

## SLSA + provenance attestations

GitHub natively emits SLSA provenance attestations for release artefacts:

```yaml
- uses: actions/attest-build-provenance@<full-sha>
  with:
    subject-path: dist/*.whl

- uses: actions/attest-build-provenance@<full-sha>
  with:
    subject-path: |
      app.tar.gz
      ./dist/*.tgz
```

The attestation is signed via sigstore (keyless, via the workflow's OIDC identity) and uploaded to the GitHub Attestations API. Downstream consumers verify with:

```bash
gh attestation verify dist/wheel.whl --repo ingka-digital/iidp-bimonthly-app
```

This is the SLSA Build Level 3 evidence chain.

## Verifying actions before adding them

Before a new action lands in `.github/workflows/`:

| Check | What to look for |
|---|---|
| Owner reputation | Verified publisher, or owned by a well-known maintainer / Ingka. |
| Star history, commit history | Active maintenance; no recent ownership change. |
| Permissions requested | Action README documents required permissions; matches what the workflow grants. |
| Open issues / advisories | No unresolved high-severity advisories. |
| Source review | Read the action's `action.yml` and main script; spot anomalies (shell injection, exfil patterns). |
| Pinning policy | Tag scheme suitable for SHA pinning; tags re-tagged frequently are a red flag. |

## tj-actions / reviewdog post-mortem

The `tj-actions/changed-files` compromise in 2024 (and the reviewdog token-leak event earlier) both succeeded because workflows pinned to `@v` tags that the attacker could redirect.

Defences in IIDP:

1. SHA pinning catches the redirected-tag attack.
2. Restricted workflow permissions (`contents: read`) prevent the compromised action from reading additional repo secrets.
3. OIDC + short-lived tokens limit blast radius to one workflow run.
4. Environment-scoped secrets prevent a feature-branch run from touching prod credentials.

## Dependabot config (minimum)

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: "/"
    schedule: { interval: weekly }
    open-pull-requests-limit: 10

  - package-ecosystem: pip
    directory: "/"
    schedule: { interval: daily }
    cooldown:
      default-days: 7

  - package-ecosystem: npm
    directory: "/frontend"
    schedule: { interval: daily }
    cooldown:
      default-days: 7
```

The `cooldown` block defers brand-new package versions for seven days (NPM compromise window).

## Wiz / JFrog / Defender for DevOps integration

- Wiz Code (or equivalent) scans the repo for IaC misconfigurations; results posted as PR comments.
- JFrog Xray scans built artefacts (per [01-supply-chain.md](01-supply-chain.md)) and gates promotion to prd remote.
- Defender for DevOps (Azure-side) connects to the GitHub org and surfaces findings in the Azure portal alongside CSPM findings.

These are tenant-installed and emit results to the team; the repo's job is not to suppress findings without justification.

## Common gaps to flag

| Severity | Finding | Fix |
|---|---|---|
| Blocker | Third-party action pinned to a tag or branch. | Pin to full SHA; add Dependabot for `github-actions`. |
| Blocker | `permissions: write-all` or absent workflow-level `permissions:`. | Set `contents: read` at workflow level. |
| Blocker | Long-lived cloud / registry credential in `secrets`. | Switch to OIDC federation. |
| Blocker | `app-prd` environment without required reviewer. | Configure approver list. |
| High | No GitHub Dependency Review action. | Add. |
| High | No SLSA / build provenance attestation on release artefacts. | Add `attest-build-provenance`. |
| High | No tag-protection rule on `v*`. | Add. |
| Medium | Dependabot config missing `github-actions` ecosystem. | Add. |
| Medium | New action added without verification trail (owner, permissions). | Document in PR description. |
| Low | CODEOWNERS missing security path coverage. | Extend. |
| Info | Repo has GHAS license but features (push protection, validity checks) not enabled. | Enable in repo settings. |

## What to grep for in a PR

```bash
rg -n '^\s*-\s*uses:.*@v\d+($|/|\s)' .github/                # tag pin
rg -n '^\s*-\s*uses:.*@(main|master|HEAD)' .github/          # branch pin
rg -nE 'permissions:\s*(write-all|.+:\s*write\b)' .github/   # broad permissions
rg -n 'AZURE_CLIENT_SECRET|AWS_SECRET_ACCESS_KEY' .github/   # long-lived creds
test -f .github/dependabot.yml && cat .github/dependabot.yml | rg github-actions
```

## Maturity rubric (1–4)

| Score | Description |
|---|---|
| 1 | Actions pinned to `@v` or branches. `secrets.AZURE_CLIENT_SECRET` in workflows. No environments. |
| 2 | Some SHA pinning; OIDC for one or two repos. Environments exist but no approvers. |
| 3 | All `uses:` SHA-pinned with comments. Workflow-level `permissions: contents: read`. OIDC for every cloud / registry call. `app-prd` environment with required reviewers + tag-protection rule. CODEOWNERS covers `.github/`, auth, infra. Dependabot covers all ecosystems including `github-actions`. |
| 4 | Above, plus SLSA Build L3 attestations on every release, push protection + custom patterns + validity checks enabled, Defender for DevOps connected, quarterly review of action allowlist. |

## Cross-references

- [01-supply-chain.md](01-supply-chain.md) — Python and npm side of supply chain.
- [02-secrets.md](02-secrets.md) — Gitleaks + OIDC.
- [06-ci-cd.md](06-ci-cd.md) — PR gate matrix.
- `ii-dig-iidp-infra/docs/security/06-supply-chain.md`.
