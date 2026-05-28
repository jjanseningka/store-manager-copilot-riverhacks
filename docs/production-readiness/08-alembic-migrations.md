# 08 — Alembic migrations

> Trust boundary: schema changes that ship with code. Backwards-incompatible migrations are the second-most-common cause of failed prod deploys (after credential rotation drift).

## Source of truth

- IIDP skill: [`iidp-alembic-migrations`](../../skills/iidp-alembic-migrations/SKILL.md) — mandatory workflow, idempotent patterns with PostgreSQL `DO` blocks, ENUM handling, materialized views, data migrations, schema utilities.
- `ii-dig-iidp-infra/scripts/grant_deployer_spn_lakebase.py` (cited in `01-identity.md`) — the SPN that runs migrations holds the `iidp_db_admins` group role, not table ownership directly.

## Single head per branch

Alembic supports branched migration histories, but most IIDP projects do not need them. Keep one head.

```bash
$ alembic heads
2024_05_20_b3a4c1d_add_orders_table (head)
```

If `alembic heads` returns >= 2, two PRs created migrations from the same parent and one was merged without rebasing. Resolve before merging the second PR:

```bash
$ alembic merge -m "merge heads" <rev1> <rev2>
```

But: never merge heads silently. Re-base the newer PR on `main`, regenerate the migration, and force the head to chain.

## `upgrade()` / `downgrade()`

Every revision has both. `downgrade()` is the rollback contract.

```python
def upgrade() -> None:
    op.add_column("orders", sa.Column("priority", sa.Integer(), nullable=True))
    op.execute("UPDATE orders SET priority = 0 WHERE priority IS NULL")
    op.alter_column("orders", "priority", nullable=False)


def downgrade() -> None:
    op.drop_column("orders", "priority")
```

Anti-patterns:

- `def downgrade(): pass` — there is no rollback. If the upgrade fails partway, the database is wedged. Either implement downgrade, or declare the migration irreversible **in writing**, in the docstring, with a runbook reference.
- Raising `NotImplementedError` in `downgrade()` — same problem.
- A downgrade that data-loses without warning. Document and gate.

## Idempotent ENUM (Postgres)

Postgres ENUM types are global and survive ROLLBACK in some cases. Use `DO` blocks to make migrations re-runnable:

```python
def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'order_status'
            ) THEN
                CREATE TYPE order_status AS ENUM ('pending', 'shipped', 'cancelled');
            END IF;
        END $$;
        """
    )
    op.add_column("orders", sa.Column("status", sa.Enum("pending", "shipped", "cancelled",
                                                        name="order_status",
                                                        create_type=False),
                                      nullable=False, server_default="pending"))


def downgrade() -> None:
    op.drop_column("orders", "status")
    op.execute("DROP TYPE IF EXISTS order_status;")
```

Similarly idempotent: index creation (`CREATE INDEX IF NOT EXISTS`), constraint adds (`DO $$ ... pg_constraint`).

## Expand-then-contract for non-backwards-compatible changes

The deployment sequence is: deploy new code that supports both old and new schema → run migration → deploy code that only supports new schema. Two PRs, two migrations.

**Column rename** (example: `user_email` → `email`):

1. PR 1 — migration adds `email`, copies from `user_email`, keeps both. Application reads from either column.
2. Deploy PR 1.
3. PR 2 — migration drops `user_email`. Application reads from `email` only.
4. Deploy PR 2.

**Type change** (example: `amount NUMERIC(10,2)` → `NUMERIC(12,4)`):

1. Migration A — `ALTER COLUMN amount TYPE NUMERIC(12,4)` (Postgres widens in-place if possible). One-shot if no app-side change is needed; otherwise expand-then-contract.

**Drop a not-null column**:

1. PR 1 — make nullable; application stops writing to it.
2. Deploy.
3. PR 2 — drop.

## Long-running migrations on large tables

Anything that takes a table lock for more than ~1 second is a production incident.

- Add an index with `CREATE INDEX CONCURRENTLY` (cannot run inside a transaction; use `op.execute` outside `with op.batch_alter_table` and set `transactional_ddl = False` in `alembic.ini` for that revision).
- Backfill in batches (`UPDATE ... WHERE id BETWEEN x AND y` in a loop), not a single statement.
- Add a `CHECK` constraint as `NOT VALID` first, then `VALIDATE CONSTRAINT` in a second migration.

## Dev/prod schema isolation

- Migrations apply to the per-env database, not a shared schema.
- Test the migration against a dev database first; staging if available. Capture wall-clock time.
- Production runs the migration via the deployer SPN, which inherits from the `iidp_db_admins` `NOLOGIN` role (per `01-identity.md`). Table ownership is the group, not the SPN — rotating the SPN does not orphan tables.

## Testing migrations in CI

Required job in PR workflow:

```yaml
- name: Alembic upgrade + downgrade
  run: |
    poetry run alembic upgrade head
    poetry run alembic downgrade base
    poetry run alembic upgrade head
  env:
    DATABASE_URL: postgresql://test:test@localhost:5432/ci_test
```

Failure cases caught:

- `downgrade()` doesn't reverse `upgrade()`.
- Migration is not idempotent (re-applying head after a downgrade fails).
- ENUM left over after downgrade.

For integration tests with real data, use `pytest-postgresql` and load a fixture dataset before applying head.

## Data migrations vs schema migrations

Separate where possible.

- **Schema migration** — Alembic revision. Fast, runs before the new code rolls out.
- **Data migration** — Backfill job, idempotent, can be re-run. Lives in a script, gated by a feature flag in the app.

If a single migration must do both (rare), bound the data step with a row count limit and a guard:

```python
def upgrade() -> None:
    op.add_column("orders", sa.Column("priority", sa.Integer(), server_default="0"))
    # Bound the data backfill to avoid runaway locks.
    op.execute("UPDATE orders SET priority = 0 WHERE priority IS NULL LIMIT 100000;")
    # Re-run as a follow-up if the table is bigger.
```

## Rollback runbook

Every destructive migration ships with a runbook entry (see [11-docs-runbooks.md](11-docs-runbooks.md)) covering:

- How to detect that the rollback is needed (symptom, log query, alert).
- The exact commands to roll back (`alembic downgrade -1` and any data-restore steps).
- Who to notify, and how to communicate to users (if user-visible).
- The recovery time objective.

## Common gaps to flag

| Severity | Finding | Fix |
|---|---|---|
| Blocker | `def downgrade(): pass` on a non-trivial upgrade. | Implement, or mark irreversible in writing with a runbook. |
| Blocker | Multiple heads (`alembic heads` >= 2). | Rebase the second PR; regenerate the migration. |
| Blocker | ENUM created without `DO` block; migration fails on re-run. | Wrap in idempotent `DO $$`. |
| Blocker | Destructive change (drop column, drop table) without expand-then-contract. | Split into two PRs. |
| High | Migration takes a long lock on a large table. | Use `CONCURRENTLY` or batched backfill. |
| High | No CI step running `upgrade → downgrade → upgrade`. | Add the job above. |
| High | Migration script touches tables it doesn't own (cross-schema). | Move to the correct migration root. |
| Medium | Data migration mixed with schema migration in one revision. | Split. |
| Medium | No rollback runbook for destructive change. | Add to `docs/runbooks/migrations/`. |
| Low | `op.execute` with raw SQL that could be SQLAlchemy-native. | Use SA helpers where possible for portability. |
| Info | Long-form revision name not matching `<date>_<topic>` pattern. | Conform. |

## What to grep for in a PR

```bash
rg -n 'def downgrade\(\)' alembic/versions/ | rg -v 'pass$'   # which downgrades exist?
rg -n 'def downgrade\(\):\s*pass' alembic/versions/           # empty downgrades
rg -n 'CREATE TYPE' alembic/versions/                         # ENUM creation
rg -n 'op\.drop_(column|table)' alembic/versions/             # destructive ops
rg -n 'op\.execute' alembic/versions/                         # raw SQL
alembic heads                                                 # how many heads
```

## Maturity rubric (1–4)

| Score | Description |
|---|---|
| 1 | Schema changes hand-applied to prod. No Alembic, or Alembic with no `downgrade()`. |
| 2 | Alembic in place. Most revisions have `downgrade()`. ENUM handling ad-hoc. No CI test. |
| 3 | Single head, `upgrade()`/`downgrade()` symmetric, idempotent ENUM, expand-then-contract on destructive changes, CI tests `upgrade → downgrade → upgrade`, runbooks for destructive migrations. |
| 4 | Above, plus migrations time-budgeted (no locks > 1s), data migrations separated, blue-green deploys verify both old and new code against the new schema, schema-snapshot diff posted in PR. |

## Cross-references

- [10-azure-infra.md](10-azure-infra.md) — Lakebase / PostgreSQL provisioning.
- [11-docs-runbooks.md](11-docs-runbooks.md) — rollback runbook.
- [`iidp-alembic-migrations`](../../skills/iidp-alembic-migrations/SKILL.md) — IIDP patterns including materialized views and schema utilities.
