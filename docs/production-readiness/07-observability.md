# 07 — Observability

> Trust boundary: ability to know what is happening in production without redeploying. Without good logs, traces, and SLOs, every incident degrades into guesswork.

## Source of truth

- Ingka IIDA Engineering Framework (Confluence `IIDA/970860277`): "Monitoring and alerting rules in place. Error logs in place and able to identify infra logs from pipelines. **Use logging instead of prints.**"
- `ii-dig-iidp-infra/docs/security/03-resources.md` — Log Analytics Workspace defaults (`retention_in_days=30`, `internet_ingestion_enabled=true`, `internet_query_enabled=true`), diagnostic settings categories, dual-sink (LAW + storage).
- IIDP skill: [`iidp-performance-debugging`](../../skills/iidp-performance-debugging/SKILL.md) — structured logging, request timing middleware, LRU caching, slow-query detection.
- External: Google SRE PRR concerns (Capacity / Change management / Dependencies / Emergency response), Azure WAF OE:07 (Workload monitoring) and RE:10 (Health monitoring).

## Structured JSON logs

One JSON event per line. No PII (email beyond `@<domain>`, name, address, financial data) without explicit classification. No secrets, no tokens, no full request bodies.

```python
import logging
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    cache_logger_on_first_use=True,
)
log = structlog.get_logger()

log.info("order.created",
         order_id=order.id, user_id=user.id, total_cents=total,
         duration_ms=duration)
```

Required fields on every event:

| Field | Source |
|---|---|
| `timestamp` | ISO 8601 UTC |
| `level` | DEBUG / INFO / WARNING / ERROR / CRITICAL |
| `event` | Dot-separated event name (e.g. `auth.login.failed`) |
| `service` | Service / app name |
| `env` | `dev` / `tst` / `prd` |
| `request_id` | Correlation ID (see below) |
| `user_id` | When known and the route is authenticated |

Anti-patterns:

- `print(...)` — never in IIDP code.
- `log.info(f"User {user.email} created order {order.id}")` — interpolated string; not queryable, leaks PII.
- Logging a stack trace via `repr(exception)` instead of structlog's `dict_tracebacks` processor.
- Logging the full request body or response body.

## Correlation ID propagation

Middleware injects an ID per request; downstream calls forward it.

```python
import uuid
import structlog

@app.middleware("http")
async def request_id_mw(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=rid)
    try:
        response = await call_next(request)
    finally:
        structlog.contextvars.clear_contextvars()
    response.headers["X-Request-ID"] = rid
    return response
```

Outgoing HTTP calls forward the header:

```python
async with httpx.AsyncClient(headers={"X-Request-ID": rid}) as client:
    ...
```

## `/healthz` vs `/readyz` (see also [03-fastapi-production.md](03-fastapi-production.md))

- `/healthz` — process is alive. No external calls. Failure restarts the container.
- `/readyz` — ready to serve. Checks DB + downstream services. Failure pulls the instance out of the LB but does not restart.

Both endpoints unauthenticated. Both return JSON. Both have a hard timeout shorter than the platform probe timeout.

## Request-timing middleware

Slow-request detection feeds the latency SLO and surfaces regressions.

```python
import time
SLOW_REQUEST_MS = 1000

@app.middleware("http")
async def timing_mw(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = int((time.perf_counter() - start) * 1000)
    response.headers["X-Response-Time-ms"] = str(duration_ms)
    log_fn = log.warning if duration_ms > SLOW_REQUEST_MS else log.info
    log_fn("http.request",
           method=request.method, path=request.url.path,
           status=response.status_code, duration_ms=duration_ms)
    return response
```

## SLOs and SLIs

Define SLOs per service. Minimum set:

| SLI | SLO target (default) | Burn-rate alerts |
|---|---|---|
| Availability (HTTP 2xx/3xx ratio) | 99.5% over 30 days | 14.4× × 1h; 6× × 6h |
| Latency p95 (read routes) | < 300 ms | Alert above 500 ms × 10 min |
| Latency p99 (write routes) | < 1500 ms | Alert above 2 s × 10 min |
| Error rate | < 0.5% 5xx over 5 min | Page above 2% × 5 min |
| Health check | `/readyz` 200 over 30 days | Page after 2 failed probes |

Sources for SLO design: Google SRE Workbook chapters 1–5, Azure WAF RE:04 (Reliability targets). Define error budgets and use them to gate releases.

## Log levels — when to use what

| Level | Use |
|---|---|
| DEBUG | Local dev only. Off in dev/tst/prd unless temporarily debugging an incident. |
| INFO | Normal request flow, business events (created, updated, deleted). |
| WARNING | Recoverable problem: retry succeeded, fallback used, slow request, deprecation. |
| ERROR | Caught exception that affected one request but not the service. |
| CRITICAL | Service-wide failure: DB unreachable, secret rotation overdue, queue saturated. |

`LOG_LEVEL` env var per env (typically `INFO` in prd; `DEBUG` only during incident windows, reset before close).

## Error tracking

Integrate one of:

- Microsoft Application Insights / Azure Monitor (preferred for Azure-hosted apps).
- Defender for Cloud for security events (already in place at tenant scope per `12-ingka-shared-services.md`).
- Sentry (for repos that need rich client-side stack traces and have approval to send data outside the tenant).

Configuration:

- Source-map upload on every prod build (for frontend); not served to the browser.
- PII scrubbing rules configured (strip `email`, `name`, `address`, etc.).
- Sample rate aligned to plan (100% errors; 5–10% transactions in prd).

## Log retention and routing

Per `03-resources.md`, every IIDP resource has dual-sink diagnostic settings (Log Analytics Workspace + storage account). LAW defaults today (RISK-14):

| Setting | Default | Recommended |
|---|---|---|
| `retention_in_days` | 30 | 90 in prd, 180 for audit-relevant tables |
| `internet_ingestion_enabled` | true | true (required for agents off-network) |
| `internet_query_enabled` | true | **false** (force VNet / private query) |
| `cmk_for_query_forced` | false | true once Ingka KMS hierarchy exists |
| `daily_quota_gb` | unset | set per service to bound cost |

Application logs typically reach LAW via the platform (Databricks Apps, App Service). Confirm the resource's diagnostic setting routes the right categories.

## Audit logs (security-relevant events)

Separate logger or separate event name space for events that must survive cost-saving log purges:

- Authentication success / failure with `user_id`, IP, user-agent.
- Authorisation denial (403) with route, principal, group memberships.
- Privilege changes (admin grant, secret rotation, role assignment).
- Data export, bulk delete, anything that could be subject to forensic review.

Audit logs go to a separate LAW table or a dedicated storage account with longer retention and stricter RBAC.

## Common gaps to flag

| Severity | Finding | Fix |
|---|---|---|
| Blocker | PII (email, name, address) logged on every request. | Strip before logging; scrub in error tracker. |
| Blocker | Secrets / tokens visible in logs. | Mask at logger config; verify with a sample query. |
| Blocker | No `/healthz` or `/readyz`. | Add (see [03](03-fastapi-production.md)). |
| High | `print()` in source. | Convert to structured logger. |
| High | Logs as free-text strings (not key=value JSON). | Use structlog or `logging.JSONFormatter`. |
| High | No correlation-ID middleware; logs cannot be joined per request. | Add the middleware above. |
| High | No SLO defined; no error budget; no alerting policy. | Define minimum SLO set; configure burn-rate alerts. |
| High | LAW `retention_in_days <= 30` for prd. | Raise to 90 days. |
| Medium | `internet_query_enabled = true` on LAW. | Set to false (force VNet query). |
| Medium | No request-timing middleware. | Add. |
| Medium | DEBUG enabled in prd. | Default to INFO; gate DEBUG by ENV. |
| Low | Audit logs share table with general INFO. | Split into a separate event namespace. |
| Info | No source-map upload to error tracker. | Configure upload step in build. |

## What to grep for in a PR

```bash
rg -n '\bprint\(' app/ src/                         # use logger
rg -n 'logger\.(info|warning|error)\(f"' app/       # f-string interpolation
rg -n 'log\.\w+\(.*password\|secret\|token' app/    # likely leak
rg -nE 'X-Request-Id' app/ frontend/                # is the ID propagated?
rg -n 'retention_in_days\s*=\s*30\b' --type tf      # short retention on prd
rg -n 'internet_query_enabled\s*=\s*true' --type tf # LAW exposed for query
```

## Maturity rubric (1–4)

| Score | Description |
|---|---|
| 1 | `print()` everywhere. No correlation IDs. No SLOs. No `/readyz`. |
| 2 | Plain-text logs to stdout. `/healthz` only. Logs go to LAW but no retention tuning. |
| 3 | JSON logs with correlation IDs. Both health endpoints. Request-timing middleware. SLOs defined and alerted on. Error tracker integrated. |
| 4 | Above, plus error budgets gating releases, audit logs separated, source maps uploaded, log queries reviewed in incident post-mortems. |

## Cross-references

- [03-fastapi-production.md](03-fastapi-production.md) — health endpoints, middleware.
- [10-azure-infra.md](10-azure-infra.md) — diagnostic settings, LAW config.
- [11-docs-runbooks.md](11-docs-runbooks.md) — incident runbook references log queries.
- [`iidp-performance-debugging`](../../skills/iidp-performance-debugging/SKILL.md).
