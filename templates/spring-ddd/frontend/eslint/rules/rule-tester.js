import path from 'node:path'
import { RuleTester } from 'eslint'
import tseslint from 'typescript-eslint'
import { afterAll, describe, it } from 'vitest'

RuleTester.afterAll = afterAll
RuleTester.describe = describe
RuleTester.it = it
RuleTester.itOnly = it.only

const fixtures = path.join(import.meta.dirname, 'fixtures')
const filename = path.join(fixtures, 'file.tsx')

/**
 * A RuleTester whose cases are type-checked as `fixtures/file.tsx`, with React's types in scope.
 *
 * `disallowAutomaticSingleRunInference`: with `CI=true` typescript-eslint assumes a one-shot lint
 * and builds the program once, so every case after the first is checked against stale types.
 */
export function typedRuleTester() {
  const tester = new RuleTester({
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        project: './tsconfig.json',
        tsconfigRootDir: fixtures,
        ecmaFeatures: { jsx: true },
        disallowAutomaticSingleRunInference: true,
      },
    },
  })
  const asFile = (testCase) => ({ ...(typeof testCase === 'string' ? { code: testCase } : testCase), filename })
  return {
    run(name, rule, { valid, invalid }) {
      tester.run(name, rule, { valid: valid.map(asFile), invalid: invalid.map(asFile) })
    },
  }
}
