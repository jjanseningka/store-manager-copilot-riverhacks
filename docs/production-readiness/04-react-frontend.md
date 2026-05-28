# 04 — React frontend

> Trust boundary: what JavaScript reaches the user's browser, how much, and what it can read. Front-end posture is mostly about supply chain (covered in [01](01-supply-chain.md) and [02](02-secrets.md)) plus runtime hygiene (no `console.log`, no inline scripts, no unsanitised HTML, no oversized bundle).

## Source of truth

- Ingka IIDA Engineering Framework (Confluence `IIDA/970860277`): "Track user experience for performance and load time expectations."
- IIDP skill: [`iidp-react-typescript-patterns`](../../skills/iidp-react-typescript-patterns/SKILL.md) — functional components, custom hooks, code splitting, lazy loading, error boundaries.
- IIDP skill: [`iidp-webpack-build-process`](../../skills/iidp-webpack-build-process/SKILL.md) — dev/prod build commands, minification safety rules.
- IIDP skill: [`iidp-skapa-ui-standards`](../../skills/iidp-skapa-ui-standards/SKILL.md) — Skapa React components only (never web components).

## TypeScript discipline

- TypeScript strict mode on. `tsconfig.json` includes `"strict": true`, `"noImplicitAny": true`, `"noUncheckedIndexedAccess": true`, `"exactOptionalPropertyTypes": true`.
- `any` is a finding. Use `unknown` plus narrowing, or a domain interface.
- API responses validated at the boundary with `zod`, `io-ts`, or a typed fetch wrapper. Browser code never trusts a JSON shape blindly.
- Props interfaces named `<Component>Props`. Optional fields use `?`, never `| undefined` (consistency).

## Routing and code splitting

```tsx
import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";

const Homepage = lazy(() => import("./pages/Homepage"));
const AzureBOM = lazy(() => import("./pages/AzureBillOfMaterials"));

export const AppRoutes = () => (
  <Suspense fallback={<PageSpinner />}>
    <Routes>
      <Route path="/" element={<Homepage />} />
      <Route path="/azure-bom" element={<AzureBOM />} />
    </Routes>
  </Suspense>
);
```

Anti-patterns:

- All routes statically imported at the top of `App.tsx` (defeats code splitting).
- Vendor chunks not separated (`webpack splitChunks: { chunks: "all" }` not set).
- Static `import` of a heavy library used only on one page (Recharts, Monaco, Mermaid).

## Bundle budgets

Set explicit budgets in CI. Example for Webpack:

```js
// webpack.config.js (prod)
module.exports = {
  performance: {
    maxAssetSize: 250 * 1024,        // 250 KB per asset
    maxEntrypointSize: 250 * 1024,   // 250 KB initial JS
    hints: "error",                  // fail the build
  },
};
```

Or with `@bundlewatch/cli`:

```json
"bundlewatch": {
  "files": [{ "path": "dist/main.*.js", "maxSize": "250 KB" }]
}
```

Run on PRs; fail the build if exceeded. Common offenders: Moment.js (use date-fns or native `Intl`), Lodash (use the per-function imports), Material-UI in addition to Skapa (pick one), full Mermaid bundle on a page that doesn't render diagrams.

## Production hygiene

- `console.log`, `debugger`, and `alert` are stripped in prod builds. Configure the bundler to drop them:
  - Webpack + Terser: `compress: { drop_console: true }` in Terser plugin.
  - Vite/Rollup: `terserOptions.compress.drop_console = true`.
- ESLint `no-console: ["error", { allow: ["warn", "error"] }]` so they don't sneak back in.
- Source maps in prod uploaded to error tracking (Sentry / App Insights) but not served to the browser.
- No client-side `fetch('/...', { credentials: 'include' })` to a different origin without explicit CORS contract.

## No `dangerouslySetInnerHTML` without sanitisation

If absolutely required (rendering Markdown or HTML produced upstream):

```tsx
import DOMPurify from "dompurify";
const safe = DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
return <div dangerouslySetInnerHTML={{ __html: safe }} />;
```

Better: render Markdown via `react-markdown` with default disallowed HTML; or keep the data structured and render with components.

## Content Security Policy

Server returns a CSP header (set in the backend or ingress, not in a `<meta>` tag — `<meta>` cannot block `frame-ancestors`):

```text
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'nonce-<random>';
  style-src 'self' 'unsafe-inline';      # acceptable for Skapa today
  img-src 'self' data: https://*.ingka-skapa.com;
  connect-src 'self' https://api.<env>.iidp.ingka.com;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
```

Notes:

- `'unsafe-inline'` on styles is acceptable while Skapa still emits inline styles; revisit when Skapa supports nonces.
- No inline `<script>` blocks. Use `<script nonce="...">` if absolutely needed.
- `frame-ancestors 'none'` unless the app must be iframed; in that case, allowlist explicitly.

## React Skapa rules (IIDP)

- Use the React components from `@ingka/*` only. Never use the Skapa web components in the same React tree — the [`iidp-skapa-ui-standards`](../../skills/iidp-skapa-ui-standards/SKILL.md) skill explains why (event-handling mismatch, focus traps).
- Adaptive CSS variables for dark/light mode; do not hardcode hex colours.
- Icons via `@ingka/ssr-icon`.
- See the Skapa skill for the component catalog and code snippets.

## Accessibility (WCAG 2.1 AA minimum)

- Every interactive element is keyboard-reachable (Tab order, focus visible).
- Labels on form fields; ARIA attributes only when no native semantic exists.
- Colour contrast >= 4.5:1 for body text, 3:1 for large text.
- Linting: `eslint-plugin-jsx-a11y` enabled (`recommended` ruleset).

## Error boundaries

Per route, at minimum. Per major UI region for complex pages.

```tsx
class ErrorBoundary extends React.Component<Props, { error?: Error }> {
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Report to error tracker. Strip stack from user view.
    reportError(error, { componentStack: info.componentStack });
  }
  render() {
    if (this.state.error) return <FriendlyError />;
    return this.props.children;
  }
}
```

User-visible error message is non-technical. Stack traces go to the error tracker, not the DOM.

## Lockfile + install discipline

- `package-lock.json` committed; `yarn.lock` removed if migrating.
- CI install: `npm ci --ignore-scripts` (covered in [01-supply-chain.md](01-supply-chain.md)).
- `node` version pinned in `.nvmrc` or `package.json` `"engines"`.
- One package manager per repo. Mixing npm and pnpm is a finding.

## Common gaps to flag

| Severity | Finding | Fix |
|---|---|---|
| Blocker | API key, token, or DB credential bundled into the JS (use `rg -nE 'sk-\|AKIA\|API_KEY' dist/`). | Move to backend; never trust the client. |
| Blocker | `dangerouslySetInnerHTML` with user input, no sanitiser. | Use DOMPurify or render structured. |
| Blocker | CORS `*` matches a client that sends `credentials: 'include'`. | Tighten CORS (see [03](03-fastapi-production.md)). |
| High | All routes statically imported (no lazy split). | Convert to `React.lazy` + `Suspense`. |
| High | Initial JS bundle > 250 KB gzipped. | Investigate via `webpack-bundle-analyzer`; remove or lazy-load. |
| High | `console.log` in production bundle. | Configure Terser to drop; add ESLint rule. |
| High | No CSP header. | Set per the template above. |
| High | `any` used to bypass a real type error. | Fix the type or use `unknown` + narrowing. |
| Medium | Mixing two component libraries (Skapa + MUI). | Pick one. Skapa is the IIDP default. |
| Medium | No error boundary on routes. | Add per the template above. |
| Medium | No accessibility lint (`jsx-a11y`). | Enable. |
| Low | Inline styles instead of Skapa tokens. | Use `var(--colour-...)`. |
| Info | Source maps served to browser. | Upload to Sentry/App Insights; do not serve. |

## What to grep for in a PR

```bash
rg -n 'console\.(log|debug)\(' frontend/src/
rg -n 'dangerouslySetInnerHTML' frontend/src/
rg -n ': any\b' frontend/src/
rg -n 'allow_origins=\[\s*"\*"\s*\]'      # checks the backend pairing
rg -n 'import .* from\s+["@]ingka-skapa-web-components' # web-components ban
rg -n 'fetch\(.*credentials\s*:\s*["'"'"']include' frontend/src/
```

## Maturity rubric (1–4)

| Score | Description |
|---|---|
| 1 | No TS strict, no lazy routes, no bundle budget, `console.log` in prod, no CSP. |
| 2 | TS strict on. Some lazy routes. No bundle budget. CSP via `<meta>` only. |
| 3 | TS strict, lazy routes + Suspense, bundle budget gated in CI, `drop_console`, CSP header, error boundaries per route, `jsx-a11y` lint. |
| 4 | Above, plus a11y audited (axe-core in CI), source maps uploaded to error tracker, Lighthouse budgets in CI, Skapa-only component policy enforced via lint rule. |

## Cross-references

- [01-supply-chain.md](01-supply-chain.md) — npm + JFrog.
- [03-fastapi-production.md](03-fastapi-production.md) — CORS contract that must match.
- [05-testing.md](05-testing.md) — React Testing Library patterns.
- [`iidp-react-typescript-patterns`](../../skills/iidp-react-typescript-patterns/SKILL.md), [`iidp-skapa-ui-standards`](../../skills/iidp-skapa-ui-standards/SKILL.md), [`iidp-webpack-build-process`](../../skills/iidp-webpack-build-process/SKILL.md).
