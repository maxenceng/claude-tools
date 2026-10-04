# Design system

A screen says what it shows; the design system decides how it looks. `src/design-system/`
holds every visual decision the application makes — tokens, a minimal base, and a small set
of primitives — and a screen composes those primitives and nothing else.

The first version of the worked example styled each element where it stood, with the same
utility classes repeated element after element. Two screens built that way drift apart one
`mt-4` at a time, and a change of look means editing every screen. With one place for the
look, a new screen cannot be incoherent with the others, and a change of look is a change
to one token or one primitive.

## Why CSS Modules and tokens

- **CSS Modules** keep each primitive's styles in a plain `.css` file beside it, scoped by
  Vite with no configuration. It is standard CSS, so nesting, `:hover` and
  `prefers-color-scheme` need no preprocessor and no runtime.
- **Custom properties as tokens** give every value one name, readable in any module and
  overridable in one `@media` block for dark mode.
- Not Tailwind: utility classes put the styling back in the screen, which is the problem.
- Not Sass: modern CSS nests natively; a compiler adds a dependency for nothing.
- Not CSS-in-JS: it injects styles at runtime — a cost and a dependency for what a static
  stylesheet already does.
- Not a UI library: its components bring their own look and their own API, and the
  application's look becomes the library's defaults plus overrides. Eight in-house
  primitives cost less than learning one library's escape hatches, and their API is this
  project's vocabulary.

## Tokens

```css
/* src/design-system/tokens.css */
/*
 * The design tokens: every colour, space, radius, border, focus ring and type value the UI uses.
 * Primitives read these; nothing else names a raw value.
 */
:root {
  color-scheme: light dark;

  --color-text: oklch(0.21 0.01 260);
  --color-muted: oklch(0.48 0.01 260);
  --color-danger: oklch(0.5 0.19 27);
...
  --space-none: 0;
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 0.75rem;
  --space-lg: 1.5rem;
  --space-xl: 3rem;
...
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-text: oklch(0.93 0.005 260);
    --color-muted: oklch(0.72 0.01 260);
    --color-danger: oklch(0.72 0.16 27);
```

- **A token is named for its role, not its value**: `--color-danger`, not `--red-700`;
  `--space-md`, not `--space-12`. A rebrand changes values, not names.
- **Every raw value is a token.** A primitive's module contains `var(--…)` and keywords,
  never a `px`, `rem`, hex or `oklch(…)`. A value with no token gets one in `tokens.css`
  first, in the dark block too when it is a colour.
- **The spacing scale is closed.** `Space` in `Stack.tsx` is the union of its names, so a
  `gap` outside the scale is a compile error, not a review comment.

`global.css` is the base every page starts from: box-sizing, the margin reset, body colour
and type from tokens, inherited fonts on form controls, and the focus ring. `main.tsx`
imports `tokens.css` then `global.css`, once; it is the only file outside the design
system that may import a stylesheet.

## A primitive's API

```tsx
// src/design-system/Stack.tsx
import type { JSX, ReactNode } from 'react'
import styles from './Stack.module.css'

export type Space = 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl'

export interface StackProps {
  children: ReactNode
  /** Distance between children, from the spacing scale. */
  gap: Space
  direction?: 'vertical' | 'horizontal'
  align?: 'stretch' | 'start' | 'center' | 'baseline'
}

/** Lays its children out in a line, spaced by a token rather than by margins on each child. */
export function Stack({ children, gap, direction = 'vertical', align = 'stretch' }: StackProps): JSX.Element {
  return (
    <div className={styles.stack} data-gap={gap} data-direction={direction} data-align={align}>
      {children}
    </div>
  )
}
```

```css
/* src/design-system/Stack.module.css */
.stack {
  display: flex;
  flex-direction: column;

  &[data-direction='horizontal'] { flex-direction: row; flex-wrap: wrap; }

  &[data-gap='none'] { gap: var(--space-none); }
  &[data-gap='xs'] { gap: var(--space-xs); }
...
  &[data-align='baseline'] { align-items: baseline; }
}
```

Every primitive has this shape:

- **`X.tsx` and `X.module.css`, exported from `index.ts`** with its named `XProps`
  interface. Screens import from `'../design-system'`, never from a primitive's file.
- **A named props interface, `XProps`.** Lint rejects a bare `Props`, and a named interface
  is what a caller hovers to learn the API.
- **One prop per visual axis, typed as a string literal union.** `tone`, `size`, `variant`,
  `gap`, `direction`, `align`, `level`. A literal union is checked by the compiler, listed
  by the editor, and — because it is not `string` — passes the copy rule with no
  configuration (`lint.md`). A token-valued prop typed `string` loses all three.
- **No boolean modes.** `muted`, `isLink` or `horizontal` as booleans multiply: two of them
  are four combinations, some of them nonsense. One `tone` or `variant` union names each
  allowed state once (`vercel-composition-patterns`: `architecture-avoid-boolean-props`,
  `patterns-explicit-variants`).
- **A variant reaches CSS as a `data-*` attribute** on the element, and the module selects
  on it. There is one module class per element, no class-joining helper, and no
  `styles[variant]` lookup, which `noUncheckedIndexedAccess` would type as possibly
  `undefined`.
- **Defaults in the destructuring**, so the type says what is optional and the signature
  says what it falls back to. `Text` leaves `size` undefined on purpose: no `data-size`,
  and the text inherits its surroundings.
- **Content through `children`**, not `label`/`renderX` props, except where the element
  needs a string attribute (`TextField`'s `label` is a `<label>`'s text, so it is a
  `string`, and the copy rule reads a literal passed to it as copy — rightly).
- **No `className` or `style` prop.** A primitive that accepts one has an escape hatch, and
  every screen will use it. When a primitive cannot express what a screen needs, the
  primitive grows.
- **No `forwardRef`.** No primitive needs a ref yet; when one does, React 19 takes `ref` as
  an ordinary prop (`react19-no-forwardref`).
- **A `function` declaration with an explicit `JSX.Element` return type**, like every
  component; lint enforces both.

A primitive that must pass a variant straight to an element attribute narrows it to a
literal there, because the lint rule for that attribute only accepts a literal:

```tsx
// src/design-system/Button.tsx
/**
 * A button whose type is always explicit.
 *
 * `type` is narrowed to a literal in the JSX because react/button-has-type accepts only a
 * literal there, not a value passed through from a prop.
 */
export function Button({ children, type, variant = 'primary', onClick }: ButtonProps): JSX.Element {
  return (
    <button
      type={type === 'submit' ? 'submit' : 'button'}
      className={styles.button}
      data-variant={variant}
      onClick={onClick}
    >
      {children}
    </button>
  )
}
```

## Accessibility is the primitive's job

A screen should not have to remember how a live region works. The primitives that carry
semantics carry all of it:

| Primitive | Owns |
|---|---|
| `Page` | the `<main>` landmark |
| `Heading` | the outline level (`level` → `h1`–`h3`), an `id` for `aria-labelledby` |
| `Button` | a required `type`, so nothing submits a form by accident |
| `TextField` | the label tied to the input by `useId`, `aria-invalid` and `aria-describedby` only while there is an error, and the always-mounted `aria-live="polite"` error slot |
| `Alert` | `role="alert"` |
| `Status` | `role="status"` |

`TextField`'s error slot is the case that shows why: a live region announces only changes
that happen after it exists, so the slot is mounted empty and filled later. Written by hand
in each screen, it is mounted with its message sooner or later, and nothing is announced.
`TextField.test.tsx` pins it by collecting the live regions before the error appears.

A screen still owns its own structure: `<section aria-labelledby>`, `<form onSubmit>` and
the `<div aria-live="polite">` that holds the results are raw elements in
`CoursePopularity.tsx`, with no styling. Structure and semantics are allowed in a screen;
`className` and `style` are not.

## Extend a primitive, or add one

When a screen needs something no primitive renders:

1. **Compose first.** Two primitives in a `Stack` are not a new primitive. A button row is
   `<Stack direction="horizontal" gap="sm">`, not a `ButtonRow`.
2. **Extend when it is another value on an existing axis.** A destructive button is
   `variant: 'primary' | 'link' | 'danger'` and a `[data-variant='danger']` rule — not a
   `DangerButton`, and not a `danger` boolean.
3. **Add when it is a new role or new semantics.** A link (`<a href>`), a select, a list, a
   dialog: each has its own element, keyboard behaviour and accessibility, so each is its
   own primitive, with its own test for what it promises.
4. **Never restyle in the screen.** Lint stops `className` and `style` on a raw element and
   any stylesheet import outside `src/design-system/`; working around it (an inline
   `<style>`, a `data-*` attribute styled from `global.css`) is the same mistake with more
   steps.

A primitive speaks no domain language — `TextField`, never `CourseTitleField` — and the
architecture test keeps it from importing a context or `api`. If a primitive needs data,
the screen passes it in.

## Component API advice

For component API design beyond this file — compound components, lifting state, context
interfaces — invoke the `vercel-composition-patterns` skill, and the
`vercel-react-best-practices` skill for rendering and re-render rules, when they are
installed. Their Next.js and server-component rules do not apply here. One rule from
`vercel-react-best-practices` is deliberately not followed: `bundle-barrel-imports`. Its
cost comes from large third-party barrels; `index.ts` re-exports eight local modules that
Vite bundles and tree-shakes, so its cost is nil.
