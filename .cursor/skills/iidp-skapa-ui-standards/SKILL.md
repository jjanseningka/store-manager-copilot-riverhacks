---
name: iidp-skapa-ui-standards
description: >-
  Ingka Skapa design system standards: adaptive CSS variables for dark/light mode,
  React component usage (never Web Components), color mapping reference, component
  examples (Button, InputField, Card, Badge, SSRIcon). Use when working with TSX,
  CSS, or SCSS files in any Ingka/IKEA project using the @ingka/* packages.
---
# Skapa UI Standards

## CRITICAL: React Components Only

**NEVER mix React components with Web Components** — it breaks the UI.

```typescript
// ✅ CORRECT — React component import
import Button from '@ingka/button';
import { ContentCard } from '@ingka/card';
import InputField from '@ingka/input-field';
import Badge from '@ingka/badge';
import SSRIcon from '@ingka/ssr-icon';
import iconEdit from '@ingka/ssr-icon/paths/edit';

// ❌ WRONG — Web component (CSS-only import, breaks React rendering)
import '@ingka/button';
// <ingka-button>...</ingka-button>
```

---

## CRITICAL: Always Use Adaptive Colors

**NEVER use hardcoded colors.** All colors must use Skapa CSS variables that adapt to dark/light mode.

### Color Mapping Reference

| Use Case | ❌ Forbidden | ✅ Required |
|----------|-------------|------------|
| Primary background | `white`, `#ffffff`, `#f5f5f5` | `rgb(var(--colour-elevation-1))` |
| Secondary background / cards / hover | `#f5f5f5`, `#f9f9f9` | `rgb(var(--colour-elevation-2))` |
| Primary text / headings | `#000`, `#333`, `black` | `rgb(var(--colour-text-and-icon-1))` |
| Secondary text / body | `#666`, `#484848` | `rgb(var(--colour-text-and-icon-2))` |
| Tertiary text / captions / disabled | `#999`, `#9ca3af` | `rgb(var(--colour-text-and-icon-3))` |
| Borders / dividers | `#e0e0e0`, `#ddd`, `#e5e7eb` | `rgb(var(--colour-elevation-1-border))` |

### Allowed Hardcoded Colors (exceptions)

- `var(--ikea-blue, #0058a3)` — primary brand color
- `var(--ikea-red, #cc0008)` — error/destructive actions
- `rgba(0, 0, 0, 0.5)` — modal backdrop overlays
- Brand-specific: PowerBI yellow `#fff3cd`, Unity Catalog blue `#dbeafe`

---

## Implementation Patterns

### Inline Styles

```typescript
// ❌ WRONG
<div style={{ backgroundColor: 'white', color: '#333', border: '1px solid #e0e0e0' }}>

// ✅ CORRECT
<div style={{
  backgroundColor: 'rgb(var(--colour-elevation-1))',
  color: 'rgb(var(--colour-text-and-icon-1))',
  border: '1px solid rgb(var(--colour-elevation-1-border))'
}}>
```

### CSS Files

```css
/* ❌ WRONG */
.card { background-color: white; color: #333; border: 1px solid #e0e0e0; }

/* ✅ CORRECT */
.card {
  background-color: rgb(var(--colour-elevation-1));
  color: rgb(var(--colour-text-and-icon-1));
  border: 1px solid rgb(var(--colour-elevation-1-border));
}
.card:hover { background-color: rgb(var(--colour-elevation-2)); }
```

### Hover / Selected States

```typescript
// ❌ WRONG
onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#f5f5f5'; }}

// ✅ CORRECT
onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'rgb(var(--colour-elevation-2))'; }}
onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'rgb(var(--colour-elevation-1))'; }}
```

---

## Component Examples

### Button

```typescript
<Button onClick={handleClick} variant="primary" disabled={isLoading}>
  Save
</Button>
<Button onClick={onCancel} variant="secondary">Cancel</Button>
```

### InputField

```typescript
<InputField
  label="Product Name"
  value={formData.name}
  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
  error={errors.name}
  required
  placeholder="Enter product name"
/>
```

### Card

```typescript
<ContentCard>
  <ContentCard.Header><h3>Title</h3></ContentCard.Header>
  <ContentCard.Body><p>Description</p></ContentCard.Body>
  <ContentCard.Footer>
    <Button variant="primary">Action</Button>
  </ContentCard.Footer>
</ContentCard>
```

### Badge

```typescript
<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="error">Inactive</Badge>
```

### SSRIcon

```typescript
import SSRIcon from '@ingka/ssr-icon';
import iconEdit from '@ingka/ssr-icon/paths/edit';
import iconDelete from '@ingka/ssr-icon/paths/delete';

<SSRIcon path={iconEdit} size="small" />
```

---

## Finding Skapa Documentation

Use the `user-skapa-design-system` MCP server — never web search:

```
get_component("button")                          → full component docs + props
get_component("@ingka/card", includeExamples=true) → with code samples
list_components()                                → browse all available components
react_dev_help(component="button")               → React-specific usage guide
styles_dev_help()                                → CSS variables + theming reference
skapa_help()                                     → general design system overview
```

For local docs (in project): `docs/skapa/components/[component-name].md`

---

## Code Review Checklist

- [ ] No hardcoded hex colors (`#ffffff`, `#333`, etc.)
- [ ] No hardcoded named colors (`white`, `black`, `gray`)
- [ ] All backgrounds use `rgb(var(--colour-elevation-*))`
- [ ] All text uses `rgb(var(--colour-text-and-icon-*))`
- [ ] All borders use `rgb(var(--colour-elevation-1-border))`
- [ ] Only React components imported from `@ingka/*` (no web component imports)
- [ ] No `<ingka-*>` custom element tags
