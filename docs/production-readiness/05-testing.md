# 05 — Testing

> Trust boundary: claims the codebase makes about itself. A passing test suite is the cheapest production-readiness signal; a missing or shallow suite is the cheapest way to ship a regression.

## Source of truth

- Ingka IIDA Engineering Framework (Confluence `IIDA/970860277`): "Use automated tests as much as possible. **Pytest** with tests folder. Enable type checking. Use integration testing on basic parameters to prevent failed runs."
- IIDP skill: [`iidp-testing-standards`](../../skills/iidp-testing-standards/SKILL.md) — pytest fixtures, AAA pattern, async testing, mocking with `AsyncMock`, React Testing Library component and interaction testing.

## Python — pytest layout

```
src/
└── app/
    ├── controller/
    │   └── product_catalog.py
    └── services/
        └── genie_service.py
tests/
├── conftest.py
├── controller/
│   └── test_product_catalog.py
└── services/
    └── test_genie_service.py
```

Rules:

- Test paths mirror source paths. One test file per source file.
- File name is `test_<module>.py`. Function name describes the behaviour: `test_returns_empty_when_no_match`, not `test_get_product`.
- One behaviour per test. If a test asserts three things, it should usually be three tests with shared fixtures.

## AAA pattern

```python
def test_creates_user_with_default_role():
    # Arrange
    repo = InMemoryUserRepository()
    service = UserService(repo=repo)

    # Act
    user = service.create_user(email="a@b.com")

    # Assert
    assert user.email == "a@b.com"
    assert user.role == "viewer"
    assert repo.find_by_email("a@b.com") is user
```

Anti-patterns:

- Tests that call multiple service methods then assert at the end (acts like integration test, masks which step broke).
- Setup interleaved with assertions.
- `assert True` or `assert response`. Assert a specific shape.

## Async testing

Async code uses `pytest-asyncio` with `AsyncMock`. The IIDP convention is `asyncio_mode = "auto"` in `pyproject.toml`, which means tests defined as `async def` are picked up without a marker.

```python
import pytest
from unittest.mock import AsyncMock

async def test_fetches_orders_for_user():
    repo = AsyncMock()
    repo.find_by_user.return_value = [Order(id=1), Order(id=2)]
    service = OrderService(repo=repo)

    result = await service.fetch_for_user(user_id=42)

    assert len(result) == 2
    repo.find_by_user.assert_awaited_once_with(user_id=42)
```

Common mistakes:

- `Mock()` where `AsyncMock()` is needed — `await mock()` returns a coroutine that resolves to a `Mock`, not the configured value.
- Mixing sync and async fixtures.
- Forgetting to `await` an async assertion helper.

## Coverage gate

Configure in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["src/migrations/*", "src/**/__init__.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = ["pragma: no cover", "raise NotImplementedError"]
```

Targets:

- 80% line coverage minimum across the suite.
- 100% on business-logic modules (`app/controller/`, `app/services/`). Use `[tool.coverage.report] precision = 1` to surface gaps.
- 0% on generated code (`__init__.py`, Alembic migrations, generated clients).
- `# pragma: no cover` only with a one-line justification.

Branch coverage on (catches missing `else`, missing exception paths).

CI gate:

```yaml
- name: pytest
  run: pytest --cov --cov-fail-under=80 --cov-report=xml
- name: Coverage XML for SonarCloud / Codecov
  uses: codecov/codecov-action@<full-sha>
```

## Fast vs extended split

The IIDA framework calls for "integration testing on basic parameters to prevent failed runs". Split the suite so PR latency stays low.

```
tests/
├── unit/              # fast: no IO, no network, < 30s total
├── integration/       # slower: real DB (test DB), real Databricks (test workspace)
└── e2e/               # longest: full app via TestClient or Playwright
```

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
  "unit: fast, no external dependencies",
  "integration: requires test DB / sandbox Databricks",
  "e2e: end-to-end via TestClient / Playwright",
]
addopts = "-ra -q -m 'not integration and not e2e'"  # default = unit only
```

PR workflow runs unit. Nightly or main-merge workflow runs unit + integration. Pre-release runs the lot.

## Mocking externals

Unit tests never hit the network. Mock at the adapter boundary, not deep inside.

| External | Mock with |
|---|---|
| Databricks SDK | `unittest.mock.AsyncMock` on the `WorkspaceClient` methods used; or `MagicMock` for sync. |
| PostgreSQL / Lakebase | In-memory fake repository implementing the interface; or `pytest-postgresql` for integration tests. |
| HTTP (httpx) | `respx` for typed mocks. |
| MS Graph / Microsoft 365 | `pytest-httpx` or hand-rolled fakes; integration tests can use a tenant test app. |
| Time | `freezegun` (sync code) or `pytest-freezer` (async). |
| UUIDs | Inject a generator into the service; mock it. |

## FastAPI route testing

```python
from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_user_requires_auth():
    client = TestClient(app)
    response = client.post("/api/users", json={"email": "a@b.com"})
    assert response.status_code == 401
```

Dependency overrides for auth:

```python
from app.auth import require_admin

def override_admin():
    return UserContext(email="test@example.com", is_admin=True, ...)

app.dependency_overrides[require_admin] = override_admin
```

Reset overrides in a fixture's teardown to avoid leakage between tests.

## Frontend — React Testing Library

The IIDP convention is RTL over Enzyme. Test what the user sees, not implementation details.

```tsx
import { render, screen, userEvent } from "@testing-library/react";
import { ProductModal } from "./ProductModal";

test("submits the form when name and price are valid", async () => {
  const onSubmit = jest.fn();
  render(<ProductModal onSubmit={onSubmit} />);

  await userEvent.type(screen.getByLabelText(/name/i), "Lack");
  await userEvent.type(screen.getByLabelText(/price/i), "12");
  await userEvent.click(screen.getByRole("button", { name: /save/i }));

  expect(onSubmit).toHaveBeenCalledWith({ name: "Lack", price: 12 });
});
```

Rules:

- Query by accessible role / label / text, not by `data-testid` (use `testid` only as a last resort).
- `userEvent` over `fireEvent` (more realistic).
- Async assertions via `await screen.findBy*`, not `waitFor` wrappers.
- Component state assertions via DOM, not React internals.

## Test data

- Factories over fixtures: `factory-boy` (Python) or `@faker-js/faker` (JS).
- Property-based testing (`hypothesis`) for algorithmic code; not required for CRUD.
- Snapshot tests sparingly; they rot fast. Prefer explicit assertions.

## Pre-commit + CI gates

Tests are part of CI but not pre-commit (too slow). Pre-commit runs lint + format + type-check + secret scan. The Pyright type-check counts as a test for this purpose — strict-mode TypeScript and Pyright together catch the same class of bug as an integration test would for the typing dimension.

## Common gaps to flag

| Severity | Finding | Fix |
|---|---|---|
| Blocker | No tests added for new logic in the diff. | Add tests; bug fixes need a regression test that fails on `main`. |
| Blocker | `pytest` not in CI or failing tests don't block merge. | Add `pytest` step with non-zero exit on failure. |
| High | Coverage < 80% globally or < 100% on business logic. | Add tests for the uncovered branches. |
| High | Network call in a unit test. | Move to integration suite, or mock. |
| High | `Mock()` where `AsyncMock()` is required (silent test success). | Switch to `AsyncMock`; assert with `assert_awaited_once_with`. |
| Medium | No fast/integration split — full suite on every PR. | Add markers; default to `not integration`. |
| Medium | Tests assert on log strings or DB SQL. | Assert on observable behaviour. |
| Medium | RTL using `data-testid` only. | Query by role/label. |
| Low | Snapshot tests with no human review. | Convert to explicit assertions. |
| Info | Property-based tests missing on algorithmic code. | Consider `hypothesis`. |

## What to grep for in a PR

```bash
rg -n 'def test_' tests/                       # are there any tests?
rg -n 'Mock\(' tests/ | rg -v 'AsyncMock'      # potential async-mock bug
rg -n 'data-testid' frontend/src/              # over-reliance on testids
rg -n '@pytest\.mark\.skip' tests/             # skipped tests, why?
rg -n 'fail_under' pyproject.toml setup.cfg    # gate exists?
```

## Maturity rubric (1–4)

| Score | Description |
|---|---|
| 1 | No tests or tests do not run in CI. |
| 2 | Some tests; CI runs them; no coverage gate; mocking ad-hoc. |
| 3 | Pytest + RTL; AAA pattern; 80% coverage gate; fast/integration split; mocked externals; async covered. |
| 4 | Above, plus property-based tests on algorithmic code, contract tests for external APIs, performance regression tests with budgets, mutation testing on critical modules. |

## Cross-references

- [03-fastapi-production.md](03-fastapi-production.md) — FastAPI test client patterns.
- [06-ci-cd.md](06-ci-cd.md) — where the suite gates.
- [08-alembic-migrations.md](08-alembic-migrations.md) — migration testing.
- [`iidp-testing-standards`](../../skills/iidp-testing-standards/SKILL.md) — IIDP patterns.
