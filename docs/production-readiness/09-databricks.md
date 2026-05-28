# 09 — Databricks

> Trust boundary: how IIDP workloads run on Databricks workspaces. Three IIDP entry points: Databricks Apps (the portal pattern), Asset Bundles (job and pipeline deploys), and Unity Catalog grants (data plane).

## Source of truth

- Ingka IIDA Engineering Framework (Confluence `IIDA/970860277`): "Use best practices for using Delta/Spark in Databricks (e.g. avoid many small files)."
- `ii-dig-iidp-infra/docs/security/05-compute.md` — workspaces, secret scopes, Lakebase OAuth, system tables.
- `ii-dig-iidp-infra/docs/security/04-data-access.md` — Access Connector pattern, external locations, catalog grants, FGAC.
- IIDP skill: [`iidp-databricks-app-auth`](../../skills/iidp-databricks-app-auth/SKILL.md) — service principal, `X-Forwarded-Email` header, IAM scopes.
- Vendored skill: [`databricks-bundles`](../../skills/vendor/ai-dev-kit/databricks-skills/databricks-bundles/SKILL.md) — Asset / Declarative Bundles patterns.
- Vendored skill: [`databricks-app-python`](../../skills/vendor/ai-dev-kit/databricks-skills/databricks-app-python/SKILL.md) — Databricks Apps deployment.

## Asset Bundles — minimum `databricks.yml`

```yaml
bundle:
  name: iidp-bimonthly-app

include:
  - resources/*.yml

variables:
  warehouse_id:
    description: "SQL Warehouse ID; differs per env"
  workspace_host:
    description: "Workspace URL per env"

targets:
  dev:
    mode: development
    workspace:
      host: ${var.workspace_host}
    run_as:
      service_principal_name: ${var.deployer_spn_dev}
    variables:
      warehouse_id: 4b9b953939869799
      workspace_host: https://adb-XXXX.azuredatabricks.net

  prd:
    mode: production
    workspace:
      host: ${var.workspace_host}
    run_as:
      service_principal_name: ${var.deployer_spn_prd}   # distinct from dev
    variables:
      warehouse_id: c2d8df839c25e9a8
      workspace_host: https://adb-YYYY.azuredatabricks.net
```

Required properties:

- `targets:` explicitly lists `dev` and `prd` (and `tst` / `acc` when used). Never inherit a single target across envs.
- `run_as.service_principal_name` is distinct per target. A leaked dev SPN cannot deploy to prd.
- `mode: production` on prd; this turns on safety checks (e.g. removes the `[dev <user>]` prefix, requires explicit prod approval for some resources).
- `variables:` resolves env-specific values; no per-env duplicated literals.

## `bundle validate` in CI

```yaml
- uses: databricks/setup-cli@<full-sha>     # latest
- name: Bundle validate (dev)
  run: databricks bundle validate -t dev
- name: Bundle validate (prd)
  run: databricks bundle validate -t prd
```

Both targets validate on every PR. Validation catches:

- Reference to a missing secret scope.
- Reference to a missing UC catalog/schema.
- Missing required permission.
- YAML syntax errors before deploy.

## Secret scopes per environment

- One KV-backed secret scope per env. Naming: `iidp-{app}-{env}` (e.g. `iidp-bimonthly-dev`, `iidp-bimonthly-prd`).
- Never share a secret scope across envs. Cross-env reads from prd secrets in dev jobs are a frequent leak vector.
- IaC provisions the scope and the underlying KV backing. The workspace MSI reads via the Access Connector pattern documented in `04-data-access.md`.
- Application code reads via `dbutils.secrets.get(scope, key)` or `WorkspaceClient.secrets.get_secret(...)`. Never echo to logs.

## Databricks Apps — `app.yaml`

Required IAM scopes (per [`iidp-databricks-app-auth`](../../skills/iidp-databricks-app-auth/SKILL.md)):

```yaml
command:
  - gunicorn
  - -c
  - gunicorn.conf.py
  - app.main:app

env:
  - name: LOG_LEVEL
    value: INFO
  - name: AUTH_ENABLED
    value: "true"

resources:
  - name: workspace-warehouse
    sql_warehouse:
      id: ${var.warehouse_id}
      permission: CAN_USE

  - name: workspace-catalog
    uc:
      securable_type: catalog
      securable_full_name: iidp_${var.env}
      permission: USE_CATALOG
```

Required app-level scopes (set in the App settings, not `app.yaml`):

- `iam.access-control:read` — needed for the app to read `X-Forwarded-Email` group memberships via SCIM.
- `serving.serving-endpoints:read` — when calling Model Serving endpoints.
- `vectorsearch.vector-search-endpoints:read` — when calling Vector Search.
- `sql.warehouses:can_use` — implicit via the `sql_warehouse` resource above.

If the app calls `WorkspaceClient.iam.list_group_members(...)` it needs the IAM scope. Without it, the call fails 403 and group-membership-based authorisation silently classifies all users as "no access".

## Authentication model

- Production: trust `X-Forwarded-Email` only when behind the Databricks Apps platform (which strips and re-injects). Never expose the FastAPI process on another ingress.
- Local dev: `AUTH_ENABLED=false` + `DEV_USER_EMAIL=...` for a synthetic context; never set `AUTH_ENABLED=false` in any deployed env.
- Service-to-service: OAuth federated to the deployer SPN; no PATs.

See [03-fastapi-production.md](03-fastapi-production.md) for the FastAPI side of the header-trust contract.

## Jobs (Lakeflow Jobs)

In `resources/jobs.yml`:

```yaml
resources:
  jobs:
    nightly_etl:
      name: ${bundle.target}_nightly_etl
      run_as:
        service_principal_name: ${var.runtime_spn}     # distinct from deployer
      schedule:
        quartz_cron_expression: "0 0 2 * * ?"
        timezone_id: Europe/Stockholm
      email_notifications:
        on_failure: ["${var.oncall_alias}@ingka.com"]
      max_concurrent_runs: 1
      timeout_seconds: 7200
      tasks:
        - task_key: bronze_load
          notebook_task:
            notebook_path: ./notebooks/bronze.py
          job_cluster_key: small
        - task_key: silver_transform
          depends_on: [{ task_key: bronze_load }]
          notebook_task:
            notebook_path: ./notebooks/silver.py
      job_clusters:
        - job_cluster_key: small
          new_cluster:
            spark_version: 15.4.x-scala2.12
            data_security_mode: SINGLE_USER
            num_workers: 2
```

Required properties:

- `run_as.service_principal_name` — never a user. A user-owned job breaks when the user leaves.
- `email_notifications.on_failure` set; route to a distribution list, not an individual.
- `max_concurrent_runs: 1` unless the job is explicitly designed to overlap.
- `timeout_seconds` bounded.
- `data_security_mode` set (`SINGLE_USER` for SPN-owned jobs, `USER_ISOLATION` for shared interactive clusters).

## Unity Catalog grants

UC grants are first-class. See [`iidp-databricks-app-auth`](../../skills/iidp-databricks-app-auth/SKILL.md) for the IIDP group taxonomy.

- Read access: grant to `grp_iidp_team_{code}_{role}` or `grp_iidp_dp_{product}_read_{env}`.
- Write/CRUD via the FastAPI app: app's SPN has `USE_CATALOG` + `SELECT` on data tables; write paths use the SPN's KV-backed scope to authenticate as a privileged identity.
- Row filters / column masks (FGAC) on PII or financial columns. Use UC FGAC, not application-layer filtering, when the table is shared across apps.

## Lakebase

- OAuth passthrough only (no static Postgres passwords per `01-identity.md`).
- Tokens are short-lived; refresh per request or use the SDK auto-refresh.
- DDL (migrations) runs as the deployer SPN, which inherits from the `iidp_db_admins` `NOLOGIN` group role (per `01-identity.md`).
- Branching for dev/test: per the Lakebase Autoscaling pattern in [`databricks-lakebase-autoscale`](../../skills/vendor/ai-dev-kit/databricks-skills/databricks-lakebase-autoscale/SKILL.md).

## No PAT

- Workspace personal access tokens are banned in IIDP production code. They bypass tenant audit, never expire automatically, and are tied to a user.
- Use OAuth for human flows, federated SPN for service flows. The Databricks SDK auto-discovers OAuth when run inside a Databricks App / Job.

## Delta / Spark hygiene (per IIDA framework)

- Avoid many small files. Target file size ~ 128 MB to 1 GB. Use `OPTIMIZE` and `VACUUM` on hot tables on a schedule.
- Schema evolution on Delta: explicit `mergeSchema` opt-in, never implicit.
- Partition only on a column with consistent cardinality; do not partition by `event_time` alone (drives small files).
- Z-ORDER on a single column most queried. Re-`OPTIMIZE` after large writes.

## Common gaps to flag

| Severity | Finding | Fix |
|---|---|---|
| Blocker | `databricks.yml` `targets:` missing `prd`, or `prd` reuses dev `run_as`. | Add distinct prd target with its own SPN. |
| Blocker | Workspace PAT in code or in a workflow secret. | Switch to OAuth / SPN. |
| Blocker | Same secret scope referenced in dev and prd. | Split per env. |
| Blocker | App's IAM scopes missing — group-based auth silently degrades to "no access". | Configure `iam.access-control:read` in App settings. |
| High | Job owner is a user, not an SPN. | Set `run_as.service_principal_name`. |
| High | No `bundle validate` in CI. | Add for every target. |
| High | No `email_notifications.on_failure` on jobs. | Route to a DL. |
| High | App calls `WorkspaceClient` without OAuth — uses hardcoded host/PAT. | Use platform-injected credentials. |
| Medium | `max_concurrent_runs > 1` without justification. | Set 1 unless explicitly overlapping. |
| Medium | Notebook with embedded SQL secrets / hostnames. | Move to bundle variables + secret scope. |
| Medium | UC catalog grants given at user scope instead of group. | Use the `grp_iidp_*` taxonomy. |
| Low | Cluster `spark_version` pinned to a deprecated release. | Use latest LTS. |
| Info | No `OPTIMIZE`/`VACUUM` schedule on hot tables. | Add a maintenance job. |

## What to grep for in a PR

```bash
rg -n 'run_as:' databricks.yml resources/                  # SPN owners present?
rg -n 'PERSONAL_ACCESS_TOKEN|DATABRICKS_TOKEN' app/ src/   # PAT in code
rg -n 'dbutils\.secrets\.get\(' notebooks/ | head          # spot-check scope names
rg -n 'spark\.databricks\.delta\.schema\.autoMerge' .      # silent schema drift
rg -n 'mergeSchema.*true' .                                # implicit schema evo
```

## Maturity rubric (1–4)

| Score | Description |
|---|---|
| 1 | No bundles. Jobs owned by users. PATs in workflows. One workspace shared dev/prd. |
| 2 | Bundles exist but only one target. Some jobs SPN-owned. Secret scope shared. |
| 3 | `databricks.yml` with explicit dev/prd targets, distinct `run_as`, per-env secret scopes, `bundle validate` in CI, App IAM scopes set, jobs SPN-owned with on-failure alerts. |
| 4 | Above, plus UC FGAC on PII tables, Lakebase branching for dev/test, OPTIMIZE/VACUUM maintenance jobs, system tables monitored for cost and access, model-serving endpoints (if any) follow the [`databricks-model-serving`](../../skills/vendor/ai-dev-kit/databricks-skills/databricks-model-serving/SKILL.md) pattern. |

## Cross-references

- [02-secrets.md](02-secrets.md) — KV-backed secret scopes.
- [03-fastapi-production.md](03-fastapi-production.md) — `X-Forwarded-Email` trust gate.
- [10-azure-infra.md](10-azure-infra.md) — Access Connector MI provisioning.
- [`iidp-databricks-app-auth`](../../skills/iidp-databricks-app-auth/SKILL.md), [`databricks-bundles`](../../skills/vendor/ai-dev-kit/databricks-skills/databricks-bundles/SKILL.md), [`databricks-app-python`](../../skills/vendor/ai-dev-kit/databricks-skills/databricks-app-python/SKILL.md), [`databricks-lakebase-provisioned`](../../skills/vendor/ai-dev-kit/databricks-skills/databricks-lakebase-provisioned/SKILL.md).
