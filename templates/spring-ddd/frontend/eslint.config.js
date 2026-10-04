// Vercel's style guide is archived and .eslintrc-only, so its rules are rebuilt here on
// maintained plugins — at `error`, because a rule that only warns is one nobody follows.
import comments from '@eslint-community/eslint-plugin-eslint-comments/configs'
import js from '@eslint/js'
import jsxA11y from 'eslint-plugin-jsx-a11y'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import globals from 'globals'
import tseslint from 'typescript-eslint'
import local from './eslint/plugin.js'

const TYPESCRIPT = ['**/*.{ts,tsx}']
const TESTS = ['**/*.test.{ts,tsx}', 'src/test/**']
const DESIGN_SYSTEM = ['src/design-system/**']

const STYLING_ON_ELEMENTS = {
  selector: "JSXOpeningElement[name.type='JSXIdentifier'][name.name=/^[a-z]/] > JSXAttribute[name.name=/^(?:className|style)$/]",
  message: 'Styling belongs to the design system: compose src/design-system components instead of className or style.',
}

const STYLESHEET_IMPORTS = {
  patterns: [
    {
      group: ['*.css', '*.scss', '*.sass', '*.less'],
      message: 'Styling belongs to the design system: compose src/design-system components instead of importing a stylesheet.',
    },
  ],
}

const vercelReact = {
  'react/button-has-type': 'error',
  'react/function-component-definition': [
    'error',
    { namedComponents: 'function-declaration', unnamedComponents: 'function-expression' },
  ],
  'react/hook-use-state': 'error',
  'react/jsx-boolean-value': 'error',
  'react/jsx-curly-brace-presence': 'error',
  'react/jsx-fragments': 'error',
  'react/jsx-no-leaked-render': 'error',
  'react/jsx-no-target-blank': ['error', { allowReferrer: true }],
  'react/jsx-no-useless-fragment': ['error', { allowExpressions: true }],
  'react/jsx-pascal-case': 'error',
  'react/no-array-index-key': 'error',
  'react/no-unstable-nested-components': 'error',
  'react/self-closing-comp': 'error',
  'react/prop-types': 'off',
}

const vercelTypescript = {
  '@typescript-eslint/consistent-type-exports': ['error', { fixMixedExportsWithInlineTypeSpecifier: true }],
  '@typescript-eslint/consistent-type-imports': [
    'error',
    { disallowTypeAnnotations: true, fixStyle: 'inline-type-imports', prefer: 'type-imports' },
  ],
  '@typescript-eslint/explicit-function-return-type': ['error', { allowExpressions: true }],
  '@typescript-eslint/method-signature-style': 'error',
  '@typescript-eslint/naming-convention': [
    'error',
    { selector: ['typeLike', 'enumMember'], format: ['PascalCase'] },
    {
      selector: 'interface',
      format: ['PascalCase'],
      custom: { regex: '^I[A-Z]|^(Interface|Props|State)$', match: false },
    },
  ],
  '@typescript-eslint/no-unnecessary-qualifier': 'error',
  '@typescript-eslint/prefer-regexp-exec': 'error',
  '@typescript-eslint/require-array-sort-compare': ['error', { ignoreStringArrays: true }],
  '@typescript-eslint/switch-exhaustiveness-check': 'error',
}

const vercelCore = {
  'array-callback-return': ['error', { allowImplicit: true }],
  'block-scoped-var': 'error',
  curly: ['error', 'multi-line'],
  'default-case-last': 'error',
  eqeqeq: 'error',
  'grouped-accessor-pairs': 'error',
  'no-alert': 'error',
  'no-caller': 'error',
  'no-console': 'error',
  'no-constant-binary-expression': 'error',
  'no-constructor-return': 'error',
  'no-else-return': 'error',
  'no-eval': 'error',
  'no-extend-native': 'error',
  'no-extra-bind': 'error',
  'no-extra-label': 'error',
  'no-implicit-coercion': 'error',
  'no-iterator': 'error',
  'no-label-var': 'error',
  'no-labels': 'error',
  'no-lone-blocks': 'error',
  'no-new': 'error',
  'no-new-func': 'error',
  'no-new-wrappers': 'error',
  'no-octal-escape': 'error',
  'no-param-reassign': 'error',
  'no-promise-executor-return': 'error',
  'no-proto': 'error',
  'no-return-assign': 'error',
  'no-script-url': 'error',
  'no-self-compare': 'error',
  'no-sequences': 'error',
  'no-template-curly-in-string': 'error',
  'no-undef-init': 'error',
  'no-unreachable-loop': 'error',
  'no-useless-call': 'error',
  'no-useless-computed-key': 'error',
  'no-useless-concat': 'error',
  'no-useless-rename': 'error',
  'no-useless-return': 'error',
  'no-var': 'error',
  'object-shorthand': 'error',
  'prefer-const': 'error',
  'prefer-named-capture-group': 'error',
  'prefer-numeric-literals': 'error',
  'prefer-regex-literals': 'error',
  'prefer-rest-params': 'error',
  'prefer-spread': 'error',
  'prefer-template': 'error',
  'symbol-description': 'error',
  yoda: 'error',
}

export default tseslint.config(
  { ignores: ['dist/', 'node_modules/', 'src/api/generated/', 'eslint/rules/fixtures/'] },
  { linterOptions: { reportUnusedDisableDirectives: 'error' } },

  js.configs.recommended,
  { rules: vercelCore },
  { files: ['*.js', 'eslint/**/*.js'], languageOptions: { globals: globals.node } },

  {
    // A rule's test cases are source code, template literals included, held in strings.
    files: ['eslint/**/*.test.js'],
    rules: { 'no-template-curly-in-string': 'off' },
  },

  comments.recommended,
  { rules: { '@eslint-community/eslint-comments/require-description': 'error' } },

  {
    files: TYPESCRIPT,
    extends: [
      tseslint.configs.strictTypeChecked,
      tseslint.configs.stylisticTypeChecked,
      react.configs.flat.recommended,
      react.configs.flat['jsx-runtime'],
      reactHooks.configs.flat['recommended-latest'],
      jsxA11y.flatConfigs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        projectService: { allowDefaultProject: ['vite.config.ts'] },
        tsconfigRootDir: import.meta.dirname,
      },
      globals: globals.browser,
    },
    plugins: { local },
    settings: { react: { version: 'detect' } },
    rules: {
      ...vercelReact,
      ...vercelTypescript,
      // The presets leave these at `warn`; here nothing only warns.
      'react-hooks/exhaustive-deps': 'error',
      'react-hooks/incompatible-library': 'error',
      'react-hooks/unsupported-syntax': 'error',

      'local/no-literal-copy': 'error',
      'local/no-jsx-comments': 'error',
      'no-restricted-syntax': ['error', STYLING_ON_ELEMENTS],
      'no-restricted-imports': ['error', STYLESHEET_IMPORTS],
    },
  },

  {
    files: DESIGN_SYSTEM,
    rules: {
      'no-restricted-syntax': 'off',
      'no-restricted-imports': 'off',
    },
  },

  {
    // The entry point loads the design system's global stylesheets, once.
    files: ['src/main.tsx'],
    rules: { 'no-restricted-imports': 'off' },
  },

  {
    // A test renders fixture copy and asserts on it; that copy is not the product's.
    files: TESTS,
    rules: {
      'local/no-literal-copy': 'off',
      // `input.form!`: a test reaching a node it has just rendered fails loudly if it is absent.
      '@typescript-eslint/no-non-null-assertion': 'off',
    },
  },
)
