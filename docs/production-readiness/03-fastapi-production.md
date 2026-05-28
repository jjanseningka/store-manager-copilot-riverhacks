# 03 — FastAPI production posture

> Trust boundary: the request path. Most production incidents in IIDP FastAPI apps trace back to a missing worker setting, a CORS wildcard, an absent `/readyz`, or a synchronous DB call blocking the event loop. Cover these first.

## Source of truth

- Ingka IIDA Engineering Framework (Confluence `IIDA/970860277`): "All deployments through CI/CD. Monitoring and alerting rules in place. Error logs in place and able to identify infra logs from pipelines. Secure for rollback scenarios and backup."
- IIDP skill: [`iidp-fastapi-patterns`](../../skills/iidp-fastapi-patterns/SKILL.md) — router/controller/service layering, response shape, gzip, base exception classes.
- IIDP skill: [`iidp-databricks-app-auth`](../../skills/iidp-databricks-app-auth/SKILL.md) — Databricks Apps auth model (`X-Forwarded-Email` header trust).
- IIDP skill: [`iidp-performance-debugging`](../../skills/iidp-performance-debugging/SKILL.md) — PostgreSQL singleton, LRU caching, gzip, connection pooling, request timing middleware.
- `ii-dig-iidp-bimonthly-app/.cursor/rules/020-authentication.mdc` — concrete IIDP auth example.

## Worker configuration

FastAPI is ASGI; serve it with Uvicorn workers under Gunicorn for production. Pure Uvicorn without Gunicorn loses graceful restart and per-worker memory caps.

```python
# gunicorn.conf.py
import multiprocessing
import os

cpu = multiprocessing.cpu_count()

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv("WEB_CONCURRENCY", (2 * cpu) + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 60
graceful_timeout = 30
keepalive = 5

# Only enable preload if there are NO module-level mutable globals
# (no DB connection pools created at import time, no LRU caches shared
# pre-fork). Databricks Apps containers usually OK; verify with a load test.
preload_app = False

# Process management
max_requests = 1000
max_requests_jitter = 100   # avoid worker-restart stampede

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
```

Start command:

```bash
gunicorn -c gunicorn.conf.py app.main:app
```

Anti-patterns to flag:

- `--workers 1` in production (single worker = single CPU, no isolation).
- `--worker-class sync` for an async FastAPI app (blocks the event loop).
- Custom `--worker-class` without `UvicornWorker`.
- `preload_app = True` while also initialising a DB connection pool at import time (forks share file descriptors → connection storms).
- No `max_requests` — long-lived workers leak memory over days.

## `lifespan` for startup and teardown

`@app.on_event("startup")` and `@app.on_event("shutdown")` are deprecated. Use `lifespan`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await create_pool(...)
    app.state.http_client = httpx.AsyncClient(timeout=10.0)
    try:
        yield
    finally:
        await app.state.http_client.aclose()
        await app.state.db_pool.close()

app = FastAPI(lifespan=lifespan)
```

Module-level singletons (`pool = create_pool()` at import) break preload and break graceful shutdown. Move them into `lifespan`.

## Health endpoints

Two endpoints, separate concerns.

```python
from fastapi import APIRouter, status
router = APIRouter(tags=["health"])

@router.get("/healthz", status_code=status.HTTP_200_OK)
async def liveness() -> dict[str, str]:
    """Process is alive. No external calls. Used by Kubernetes / Azure App
    Service liveness probe — failure restarts the container."""
    return {"status": "ok"}

@router.get("/readyz", status_code=status.HTTP_200_OK)
async def readiness(request: Request) -> dict[str, object]:
    """Ready to serve traffic. Checks downstream dependencies. Failure
    pulls the instance out of the load balancer but does not restart."""
    checks = {
        "db": await _check_db(request.app.state.db_pool),
        "databricks": await _check_databricks(),
    }
    if not all(c["ok"] for c in checks.values()):
        raise HTTPException(status_code=503, detail=checks)
    return {"status": "ready", "checks": checks}
```

Differences that matter:

- `/healthz` must never call the database. A DB outage should not restart every container.
- `/readyz` must fast-fail (timeout < probe timeout) and must reflect actual readiness.
- Authentication should be **off** on both (Databricks Apps health probes bypass auth anyway; an authed `/readyz` causes false alarms).

## CORS — never `*` in production

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowlist,   # explicit list per env, no "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=3600,
)
```

If `allow_credentials=True` and `allow_origins=["*"]`, FastAPI raises at startup — but only if both are set together. The common bug is `allow_credentials=False` with `allow_origins=["*"]` and a cookie auth scheme; that still leaks the cookie cross-origin if the front end opts in.

## Rate limiting

Required on auth, write, and any expensive route. Use SlowAPI or starlette-limiter. Limits are per-IP and per-user (whichever is stricter).

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...): ...
```

Anti-patterns:

- Limit applied only at the gateway with no per-route override — a single bad actor monopolises an expensive route.
- Limit applied with `key_func=lambda: "global"` — affects all users.
- No exponential backoff hint in the 429 response body.

## Trusted proxies and forwarded headers

When deployed behind Databricks Apps, Azure App Service, or an ingress controller, only trust forwarded headers from the platform. The IIDP rule from `020-authentication.mdc`:

```python
# In production, only trust X-Forwarded-Email when the request arrived
# via the Databricks Apps platform (which strips and re-injects).
# Local-dev bypass is gated by AUTH_ENABLED=false + DEV_USER_EMAIL.

email = request.headers.get("X-Forwarded-Email")
if settings.auth_enabled and not email:
    raise HTTPException(status_code=401, detail="no identity header")
```

If the FastAPI process is reachable directly (NodePort, public LB), the header trust assumption breaks. Validate the deployment shape during the audit.

## Structured logging

JSON logs, one event per line, no PII, no secrets, no full request bodies. Use `structlog` or stdlib `logging.config.dictConfig`.

```python
import structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
log = structlog.get_logger()
log.info("order.created", order_id=order.id, user_id=user.id)
```

Request-id correlation middleware:

```python
@app.middleware("http")
async def request_id_mw(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=rid)
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    structlog.contextvars.clear_contextvars()
    return response
```

See [07-observability.md](07-observability.md) for the full logging policy and SLO rules.

## gzip and response shaping

Per [`iidp-fastapi-patterns`](../../skills/iidp-fastapi-patterns/SKILL.md):

```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

JSON responses follow the IIDP envelope (when the project uses it):

```json
{"data": ..., "meta": {"request_id": "...", "duration_ms": 12}}
```

## Common gaps to flag

| Severity | Finding | Fix |
|---|---|---|
| Blocker | Missing `/healthz` or `/readyz`. | Add both, separating liveness from readiness. |
| Blocker | `allow_origins=["*"]` with `allow_credentials=True`. | Explicit allowlist. |
| Blocker | Single worker in production (`-w 1`). | Set `(2 * CPU) + 1` or `WEB_CONCURRENCY`. |
| Blocker | DB password / Databricks PAT hardcoded. | See [02-secrets.md](02-secrets.md). |
| High | No rate limit on auth or write routes. | Add SlowAPI limit, 429 with backoff hint. |
| High | Sync DB call in async path (e.g. `psycopg2` not `asyncpg`). | Switch to async client or wrap with `run_in_executor`. |
| High | `print()` in source. | Use structured logger. |
| High | Headers trusted unconditionally (`X-Forwarded-Email` without auth gate). | Gate by `settings.auth_enabled`; document deploy assumption. |
| High | Module-level singletons (DB pool, HTTP client). | Move into `lifespan`. |
| Medium | gzip middleware missing. | Add with `minimum_size=1000`. |
| Medium | `max_requests` not set on Gunicorn. | Set with jitter to avoid stampede. |
| Medium | Error handler dumps stack traces to the client. | Map to `{"error": {"code": ..., "message": ...}}` in prod; log the trace server-side. |
| Low | No request-id middleware. | Add per the snippet above. |
| Info | Worker class not specified. | Set `-k uvicorn.workers.UvicornWorker`. |

## What to grep for in a PR

```bash
rg -n 'allow_origins=\[\s*"\*"\s*\]'
rg -n 'print\(' app/                     # should be logger
rg -n '@app\.on_event' app/              # deprecated; use lifespan
rg -n 'workers\s*=\s*1\b' .              # single-worker prod
rg -n '\bsync\b.*worker' .               # wrong worker class
rg -n 'X-Forwarded-Email' app/           # check trust gate
rg -n 'def\s+\w+\(.*\):\s*$' app/ | rg -v 'async '  # sync routes that look async
```

## Maturity rubric (1–4)

| Score | Description |
|---|---|
| 1 | Single Uvicorn worker. No health endpoints. CORS wildcard. `print()` everywhere. |
| 2 | Gunicorn + UvicornWorker but worker count not tuned. `/healthz` only. CORS allowlist but no rate limit. Plain-text logs. |
| 3 | Workers tuned, `lifespan`, both health endpoints, CORS allowlist, rate limit on auth+write, structured JSON logs, request-id middleware. |
| 4 | Above, plus load-tested worker count, request-timing middleware feeding SLOs, gzip + response envelope, error tracking integrated, graceful shutdown verified. |

## Cross-references

- [02-secrets.md](02-secrets.md) — header trust, auth model.
- [05-testing.md](05-testing.md) — testing FastAPI routes with `TestClient` + `AsyncMock`.
- [07-observability.md](07-observability.md) — logging, SLOs, request timing.
- [`iidp-fastapi-patterns`](../../skills/iidp-fastapi-patterns/SKILL.md), [`iidp-performance-debugging`](../../skills/iidp-performance-debugging/SKILL.md).
