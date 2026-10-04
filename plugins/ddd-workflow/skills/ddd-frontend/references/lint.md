# Lint

`eslint.config.js` is a flat config. `make fe-lint` runs it from the project root —
`make lint` inside `frontend/`, which is `eslint .` — and `make fe-ci` runs it between the
typecheck and the tests. The root's own `make lint` is the backend's formatting check, not
ESLint. Every rule is at `error`: a rule that only warns is a rule nobody follows, and a
warning cannot fail CI. Generated code (`src/api/generated/`) is ignored.

## Where the rules come from

The review of the first worked example asked for Vercel's ESLint recommendations. Those were
`@vercel/style-guide`, which Vercel archived in February 2025; it only ever shipped
`.eslintrc` configs, which ESLint 9 no longer reads by default. So the config rebuilds its
rules by hand on maintained plugins, and says so in its header:

```js
// eslint.config.js
// Vercel's style guide is archived and .eslintrc-only, so its rules are rebuilt here on
// maintained plugins — at `error`, because a rule that only warns is one nobody follows.
```

**The base presets:** `@eslint/js` recommended; typescript-eslint `strictTypeChecked` and
`stylisticTypeChecked` (type-aware, through `projectService`); eslint-plugin-react
`recommended` and `jsx-runtime`; eslint-plugin-react-hooks `recommended-latest`, which in
7.x includes the React Compiler rules (purity, refs, immutability, set-state-in-render and
the rest); eslint-plugin-jsx-a11y `recommended`. The hooks preset leaves
`exhaustive-deps`, `incompatible-library` and `unsupported-syntax` at `warn`; the config
raises them to `error`.

**Carried over from Vercel's guide,** in three objects in the config:

- `vercelReact` — `button-has-type`, `function-component-definition` (function
  declarations), `hook-use-state`, `jsx-no-leaked-render` (no `&&` rendering a `0`),
  `no-unstable-nested-components`, `no-array-index-key`, `self-closing-comp` and the rest
  of its React rules.
- `vercelTypescript` — `consistent-type-imports` (inline `type`),
  `explicit-function-return-type`, `naming-convention` (PascalCase types, no `I` prefix, no
  bare `Props`), `switch-exhaustiveness-check`, `method-signature-style` and the rest.
- `vercelCore` — its best-practice, ES6, variables and possible-errors core rules:
  `eqeqeq`, `no-console`, `no-param-reassign`, `prefer-template`, `no-else-return`,
  `prefer-named-capture-group` and the rest.

**Left out, on purpose:** `no-floating-decimal` (deprecated in ESLint 9 as formatting);
`no-implied-eval`, `prefer-promise-reject-errors` and core `no-unused-vars` (their
type-aware `@typescript-eslint` versions are already on, and `tsc` checks unused locals and
parameters); `jsx-a11y/no-onchange` (removed from the plugin). Whole files of the guide
that need a plugin the template does not install — `import`, `unicorn`, `tsdoc`, `jest`,
`vitest`, `playwright-test` — and `stylistic`, which is a formatter's job. Its `comments`
file is the exception: `@eslint-community/eslint-plugin-eslint-comments` is installed for
it (below).

## The review, as rules

Three comments in the review became three rules, scoped by file:

| Rule | Fails on | Applies to |
|---|---|---|
| `local/no-literal-copy` | a string a person reads, written as a literal | everything but tests |
| `local/no-jsx-comments` | a comment anywhere inside JSX, or an empty `{}` | everything |
| `no-restricted-syntax` + `no-restricted-imports` | `className` or `style` on an HTML element; any `.css`/`.scss`/`.sass`/`.less` import | everything but `src/design-system/`, and `main.tsx` for imports |

```js
// eslint.config.js
const STYLING_ON_ELEMENTS = {
  selector: "JSXOpeningElement[name.type='JSXIdentifier'][name.name=/^[a-z]/] > JSXAttribute[name.name=/^(?:className|style)$/]",
  message: 'Styling belongs to the design system: compose src/design-system components instead of className or style.',
}
```

The styling selector looks only at lowercase (HTML) elements. A component's `className`
prop would pass it, which is why no primitive declares one (`design-system.md`).

Magic conditions — the review's "avoid magic string and weird conditions" — have no rule.
`no-magic-numbers` flags every index and every `1`, and is ignored within a week. That one
stays a convention: name the condition (`errors.md`, `queries.md`).

## How the local rules work

The two `local/*` rules are in `eslint/rules/`, registered by `eslint/plugin.js`, each with a
RuleTester test beside it that vitest runs with the rest of the suite.

**`local/no-jsx-comments`** walks every comment in the file and reports one whose position
is inside a `JSXElement` or `JSXFragment` — `{/* … */}`, a trailing `//` in an expression, a
comment between attributes or inside an attribute's callback. An ESLint directive is not a
comment for this rule: `{/* eslint-disable-next-line rule -- why */}` is the escape hatch,
and `require-description` makes it explain itself. An empty `{}` gets its own message.

**`local/no-literal-copy`** finds string literals where copy goes, through the forms copy
hides in:

```js
// eslint/rules/copy-literals.js
/**
 * The string literals an expression can evaluate to, through the forms copy hides in:
 * `a ? 'x' : t('y')`, `detail ?? 'x'`, `'x' as string`, `` `x ${n}` `` and `'x' + n`.
 * A call is never entered, so `t('popularity.heading')` is a key, not copy.
 */
export function copyLiterals(node) {
```

It looks in three places:

- **JSX text and child expressions** — any non-blank text, and any literal `copyLiterals`
  finds in `{…}`.
- **HTML attributes a person reads or hears** — a deny-list: `alt`, `title`, `placeholder`,
  `label` and the readable `aria-*`. Every other attribute (`href`, `id`, `role`, `type`,
  `data-*`, SVG geometry) is a token and passes.
- **Component props typed for free text** — the rule asks the type checker for the prop's
  type, and reports a literal only when that type is `string` or a union holding `string`
  (`ReactNode` included):

```js
// eslint/rules/no-literal-copy.js
    /** Whether the prop this value is passed to is declared as free text: `string`, `ReactNode`, or a union holding one. */
    function takesFreeText(expression) {
      if (!checker) return false
      const type = checker.getContextualType(services.esTreeNodeToTSNodeMap.get(expression))
      if (!type) return false
      const constituents = type.isUnion() ? type.types : [type]
      return constituents.some((constituent) => (constituent.flags & ts.TypeFlags.String) !== 0)
    }
```

That is why the rule needs no allow-list of prop names. `gap="md"`, `tone="muted"`,
`type="submit"` pass because their props are literal unions; `label="Course title"` on
`TextField` fails because `label` is a `string`. The cost is the next section.

## A token prop typed `string`

A literal passed to a component prop typed `string` is reported as copy, whatever the prop
means — the rule cannot tell an `href` from a label by type alone. The message says what to
do:

> This prop is typed to take free text, so a string literal here reads as copy: render t(…)
> for text a person reads; for an id or a path, narrow the prop to a literal union, or pass
> a module-scope constant or useId().

In order of preference:

1. **Narrow the prop.** A token-valued prop should be a literal union anyway (`Space`, not
   `string`); that is the design system's convention, and the compiler then checks the
   value too.
2. **Pass a variable.** `Heading`'s `id?: string` receives `useId()` in
   `CoursePopularity.tsx`, which is not a literal. A path or URL from a module-scope
   constant passes the same way.
3. **Disable with a reason,** for the rare prop that is genuinely free-form and not copy.

## Inline disables

The escape hatch exists and is narrow:

```tsx
// eslint-disable-next-line react-hooks/incompatible-library -- watch() is read here only; no watched value reaches a memoised child
```

- `@eslint-community/eslint-comments/require-description` fails a directive with no
  `-- reason`.
- Its `recommended` set fails a file-wide `/* eslint-disable */` with no rule named, an
  unpaired disable, and a duplicate.
- `reportUnusedDisableDirectives: 'error'` fails a directive that no longer suppresses
  anything, so a stale one cannot outlive its reason.

**`react-hooks/incompatible-library`** is the rule a project is most likely to meet first.
At `error`, it fails a call into an API "which returns functions which cannot be memoized
without leading to stale UI" — TanStack Table's `useReactTable`, react-hook-form's `watch`.
The risk is real but narrow: a value from that API passed into a memoised component or hook
can go stale. Check that nothing memoised receives it, then disable on that line with the
reason, as above. Do not switch the rule off: the next such library should still be
caught.

## Known gaps

The rules miss these forms. Review still has to look for them:

- **A literal returned from a callback** — `{items.map(() => 'From a callback')}`.
  `copyLiterals` never enters a function.
- **JSX spread** — `<input {...props} />` with `props = { placeholder: 'Search' }`. The
  attribute is not in the JSX, so nothing is checked.
- **A submit input's `value`** — `<input type="submit" value="Send" />` shows `value` as its
  label, but `value` is not on the deny-list (it is data on every other input). Use the
  `Button` primitive.
- **`?inline` and dynamic CSS imports** — `import css from './x.css?inline'` does not match
  the `*.css` pattern, and `import('./x.css')` is not seen by `no-restricted-imports`.

Each was confirmed by linting a planted file. Close one with a rule only when it shows up in
a review; until then, they are listed here so a reviewer knows to look.

## ESLint 9, pinned

ESLint is pinned to `9.39.5`, not 10. `eslint-plugin-react` 7.37.5 and
`eslint-plugin-jsx-a11y` 6.10.2 declare their `eslint` peer range up to `^9`, so installing
10 fails with `ERESOLVE` unless the project sets `legacy-peer-deps`, which would hide every
other peer conflict too. npm marks 9.39.5 deprecated ("This version is no longer supported")
on install; that is the cost. Revisit when both plugins declare support for 10. Every lint
package is pinned exactly, so a preset's release cannot add a rule at `error` and fail CI
with no change to the code.

## Adding a local rule

Add one only for a convention a review has asked for more than once and no published rule
expresses.

1. Write `eslint/rules/<name>.js` and register it in `eslint/plugin.js`.
2. Write `eslint/rules/<name>.test.js`. Import `./rule-tester.js`, which wires ESLint's
   `RuleTester` to vitest; for a rule that needs types, use its `typedRuleTester()`, which
   parses each case as a TSX file with React's types. Cover each form the rule must catch
   and each near-miss it must pass. Keep its `disallowAutomaticSingleRunInference`: under
   `CI=true` typescript-eslint otherwise builds the program once, and every later case is
   type-checked against stale code — green locally, red in CI.
3. Turn it on in `eslint.config.js` at `error`, scoped to the files it is about.
4. Watch it fail: break the code the way the rule forbids, run `npx eslint <file>`, see the
   error, and put it back. A rule that has never been seen to fail is not yet evidence of
   anything.
5. `npx vitest run eslint` runs only the rule tests; `make fe-ci` runs them with
   everything.
