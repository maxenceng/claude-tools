# 11. The frontend has a design system, i18n and lint from the first screen

Date: 2026-10-04

## Status

Accepted

## Context

The first frontend worked example, `CoursePopularity.tsx` against
[ADR 10](0010-training-demonstrates-one-http-read-endpoint.md)'s endpoint, was reviewed
before it shipped. The review asked for four things the example did not have:

- **A design system first.** Each element carried its own Tailwind classes, repeated
  element after element, so two screens would drift apart and a change of look meant
  editing every screen.
- **i18n by default.** Every word on screen was an English literal in the JSX.
- **Vercel's ESLint recommendations,** and with them no comments inside JSX.
- **No magic strings or inline conditions,** such as `enabled: title.trim() !== ''` and a
  retry lambda comparing a bare count.

Each is cheap on the first screen and expensive on the twentieth, and the worked example is
what every later screen copies.

## Decision

**Styling is a design system in `src/design-system/`:** design tokens as CSS custom
properties in `tokens.css`, and a small set of primitives, each a component with a CSS
Module. Screens compose the primitives and style nothing themselves.

- CSS Modules over Tailwind, because utility classes put the styling back in the screen;
  over Sass, because modern CSS nests natively; over CSS-in-JS, because it adds a runtime
  for what a static stylesheet does.
- In-house primitives over a UI library, because a library brings its own look and API and
  the application's look becomes its defaults plus overrides. The primitives' API is this
  project's vocabulary: one string-literal-union prop per visual axis, variants as `data-*`
  attributes, accessibility owned by the primitive.

**Copy is translated through react-i18next,** in English and French from the start: one
namespace per bounded context plus `common`, keys typed from the English resources, and a
test that fails when the two languages' keys differ. The ProblemDetail's `detail` is shown
as the server wrote it; only the client's own words are translated.

**ESLint enforces both, and Vercel's rules.** `@vercel/style-guide` is archived and ships
only `.eslintrc` configs, so `eslint.config.js` rebuilds its rules on maintained plugins
(typescript-eslint type-checked, react, react-hooks with the React Compiler rules,
jsx-a11y), every rule at `error`. Two local rules in `frontend/eslint/rules/` carry what no
plugin expresses: `no-literal-copy` and `no-jsx-comments`. Styling outside the design
system is refused by `no-restricted-syntax` and `no-restricted-imports`. `make lint` is part
of `make ci`. An inline disable must give a reason.

Conditions and statuses are named: predicates in `src/api/problem.ts` and the context's
`queries.ts`, unit-tested on their own. No lint rule enforces this; `no-magic-numbers` is
too noisy to keep on.

## Consequences

**ESLint is pinned to 9.** `eslint-plugin-react` 7.37.5 and `eslint-plugin-jsx-a11y` 6.10.2
cap their `eslint` peer range at `^9`, so ESLint 10 does not install without
`legacy-peer-deps`. npm reports 9.39.5 as unsupported. Revisit when both plugins support
10; until then, an upgrade attempt fails with `ERESOLVE`, and this file is the explanation.

**The copy rule has no allow-list, and relies on prop types instead.** It asks the type
checker whether a component prop takes free text (`string`, or a union with it) and reports
a literal only there. Token props typed as literal unions (`gap`, `tone`, `variant`) pass
with no configuration. A prop typed plain `string` that is not copy — an id, a path — is
reported, and the fix is to narrow its type or pass a variable. A design-system prop typed
`string` for a token is therefore a mistake twice over.

**The rules have known gaps**, listed in `ddd-frontend`'s `references/lint.md` so review
looks for them: a literal returned from a callback, JSX spread props, a submit input's
`value`, and `?inline` or dynamic CSS imports.

Every new screen costs a locale entry per language and a primitive or variant for any look
the design system does not have yet. That is the intended cost: it is where incoherence
would otherwise come in.
