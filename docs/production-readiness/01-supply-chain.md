# 01 — Supply chain (Python + JavaScript)

> Trust boundary: third-party code reaching the build artefact. Most modern incidents (xz-utils, SolarWinds, GitHub-app token exfiltration) start here. The IIDA framework names Poetry as the default; uv is accepted as an alternative if explicitly justified.

## Source of truth

- Ingka IIDA Engineering Framework (Confluence `IIDA/970860277`): "Python Package management: **Poetry**. Code scanning is enabled on all repos. Keep track of dependencies and possible attack vectors."
- `ii-dig-iidp-infra/docs/security/06-supply-chain.md`: pre-commit toolbelt, GitHub Actions CI, JFrog OIDC pattern (currently commented out — RISK-21/22/34), state-plane vs workload-plane split.
- External: SLSA v1.2 spec, JFrog Xray + Curation docs, GitHub OpenSSF baseline.

## What "good" looks like

### Python — Poetry (default)

- `pyproject.toml` and `poetry.lock` committed together; no orphan lock.
- Lockfile is hashed (default in Poetry; verify `[metadata]` carries `content-hash`).
- Production groups: `[tool.poetry.dependencies]`. Dev/test groups: `[tool.poetry.group.dev.dependencies]`, `[tool.poetry.group.test.dependencies]`.
- Installs in CI use `poetry install --no-root --without dev` for prod images.
- Python version pinned (`python = "^3.12"`).

### Python — uv (accepted alternative)

- `pyproject.toml` and `uv.lock` committed together. `uv.lock` carries SHA-256 entries per package.
- Installs in CI use `uv sync --frozen` (no resolve at install time).
- Python version pinned via `requires-python = ">=3.12,<3.13"`.
- README states why uv was chosen instead of Poetry (typically: build speed, monorepo, or specific feature). If unjustified, this is a Medium finding against the IIDA framework default.

### Python — supply-chain scanning

- `pip-audit` or `safety` runs in CI on every PR (against the resolved lockfile, not just `pyproject.toml`).
- Bandit runs at medium severity in pre-commit and CI (config in `pyproject.toml` `[tool.bandit]`; skip `B101` assert in test files only).
- SBOM generated per build: CycloneDX format via `cyclonedx-bom` for Python, or `@cyclonedx/cyclonedx-npm` for Node. Stored as a CI artefact and pushed to JFrog Xray for ingestion.

### JavaScript — npm

- `package-lock.json` committed; never `yarn.lock` and `package-lock.json` together.
- CI install: `npm ci --ignore-scripts`. Lifecycle scripts run only for known-safe packages, and only at build time, not at install time.
- `npm audit --omit=dev` runs in CI; HIGH/CRITICAL findings block the build unless explicitly waived in `.github/audit-allowlist.json`.
- Frontend `.npmrc` points at the JFrog mirror when tenant policy mandates it (today commented-out in IIDP per RISK-22; tracked as Patch B15).

### Release-age cooldown

A fresh package version is the highest risk window (the xz-utils backdoor was caught within days of release). Adopt one:

- **Dependabot** — `.github/dependabot.yml`:
  ```yaml
  updates:
    - package-ecosystem: "pip"
      directory: "/"
      schedule: { interval: "weekly" }
      cooldown:
        default-days: 7
        semver-major-days: 14
  ```
- **Renovate** — `renovate.json`:
  ```json
  { "packageRules": [
      { "matchManagers": ["pip_requirements", "poetry", "uv", "npm"],
        "minimumReleaseAge": "7 days" } ] }
  ```

### JFrog Artifactory + Xray + Curation (when tenant-mandated)

JFrog deprecated the Xray "Block Download" feature in 2026; the equivalent gate moved to **JFrog Curation**, which evaluates policy on metadata **before** the package enters the cache. The IIDP pattern is:

- Workflow declares `permissions: { id-token: write }` for the OIDC handshake with JFrog.
- Frontend `.npmrc` and Python `pip` / Poetry / uv configured to use the JFrog mirror endpoint.
- Curation policies enforced by the tenant: license allowlist, CVE blocklist, immutable-package policy (no recently-published versions), known-bad-package blocklist.
- Xray scans on ingestion produce CycloneDX SBOMs and feed the tenant's continuous risk view.

Example workflow snippet (live in IIDP today as a commented-out block — when JFrog is enabled, uncomment and pin):

```yaml
permissions:
  id-token: write
  contents: read

- uses: jfrog/setup-jfrog-cli@<full-sha> # vX
  with:
    oidc-provider-name: github-iidp
    oidc-audience: jfrog
- run: |
    jf rt c add --interactive=false --url=$JFROG_URL --access-token=$JFROG_TOKEN ingka
    poetry config repositories.ingka $JFROG_URL/api/pypi/pypi-virtual/simple
    poetry install --no-root
```

### SLSA + sigstore (publishing builds)

- Adopt SLSA Build Level 3 for any artefact published outside the repo (PyPI, npm, container, Databricks bundle):
  - Reusable GitHub workflow generates provenance via `slsa-framework/slsa-github-generator`.
  - Permissions: `attestations: write`, `contents: read`, `id-token: write`.
  - Consumers verify with `gh attestation verify --owner=ingka-digital <artifact>` or `cosign verify-attestation`.
- For internal-only builds, Build Level 1 (provenance exists) is the minimum.

### Authority hierarchy on this surface

| Decision | Owner | Source |
|---|---|---|
| Poetry vs uv as default | Ingka IIDA team | Confluence IIDA/970860277 |
| JFrog mirror mandate | Ingka platform | `12-ingka-shared-services.md` |
| Cooldown duration | Repo owner | This doc; defaults: 7 days minor, 14 days major |
| SBOM format | Industry | CycloneDX (JFrog Xray native) |
| Publishing provenance | Repo owner | SLSA v1.2 |

## Common gaps to flag

| Severity | Finding | Fix |
|---|---|---|
| Blocker | `pyproject.toml` changed without lockfile update. | Run `poetry lock --no-update` (or `uv lock`) and commit. |
| Blocker | Lockfile has no hashes (rare in Poetry; possible with hand-edited `requirements.txt`). | Re-generate. |
| Blocker | `npm install` used in CI instead of `npm ci`. | Use `npm ci --ignore-scripts`. |
| Blocker | Workflow installs from public registry when tenant mandates JFrog. | Wire JFrog OIDC pattern. |
| High | New dependency pinned to a version younger than 7 days. | Add cooldown rule or justify. |
| High | `pip-audit` / `safety` / `npm audit` missing in CI. | Add a CI step that fails on HIGH/CRITICAL. |
| High | Bandit disabled or `--skip` includes findings beyond `B101` / `B601`. | Restore default skips; document any added skip. |
| Medium | No SBOM produced. | Add `cyclonedx-bom` or `@cyclonedx/cyclonedx-npm` step. |
| Medium | uv used without README justification. | Add a paragraph; otherwise switch to Poetry. |
| Medium | No Dependabot or Renovate config. | Add one of the two; include `github-actions` ecosystem. |
| Low | Production install pulls dev dependencies. | Use `--without dev` (Poetry) or `--no-group dev` (uv). |
| Info | SLSA Build Level 1 only on a tenant-published artefact. | Plan Level 3 if the artefact is distributed externally. |

## What to grep for in a PR

```bash
rg -n '^\s*requirements?\s*=' --type toml      # accidental requirements pin
rg -n 'npm install\b'  .github/workflows       # should be npm ci
rg -n '@v\d+($|/)' .github/workflows           # unpinned actions (also caught by 06)
rg -n 'no-verify' .github/workflows            # ban it
rg -n '\.tar\.gz|index-url\s*=' pyproject.toml # ad-hoc index pulls
```

## Maturity rubric (1–4)

| Score | Description |
|---|---|
| 1 | Loose. No lockfile or lockfile out-of-date. No SCA scan. Installs from public registries. |
| 2 | Lockfile committed. `pip-audit` or `npm audit` runs but doesn't gate. No cooldown, no SBOM. |
| 3 | Lockfile committed, hashed, frozen install in CI. SCA scan gates. Cooldown rule active. SBOM generated. Dependabot or Renovate active. |
| 4 | Above, plus JFrog Curation gates ingestion, SLSA Build Level 3 provenance for published artefacts, `gh attestation verify` in consumers, tenant SOC ingests SBOMs. |

## Cross-references

- [02-secrets.md](02-secrets.md) — supply chain that injects secrets safely.
- [06-ci-cd.md](06-ci-cd.md) — where SCA gates run.
- [14-github-supply-chain.md](14-github-supply-chain.md) — full GitHub Actions hardening including SLSA pattern.
- [15-ingka-engineering-baseline.md](15-ingka-engineering-baseline.md) — JFrog mandate, tenant policy.
- `ii-dig-iidp-infra/docs/security/06-supply-chain.md` — live IIDP example with risks named.
