import { RuleTester } from 'eslint'
import rule from './no-jsx-comments.js'
import './rule-tester.js'

const tester = new RuleTester({
  languageOptions: { parserOptions: { ecmaFeatures: { jsx: true } } },
})

tester.run('no-jsx-comments', rule, {
  valid: [
    '// explains the view\nconst view = <div>{x}</div>',
    'const view = (\n  // explains the view\n  <div />\n)',
    '/* a */ const view = <><span id="a" /></>',
  ],
  invalid: [
    { code: 'const view = <div>{/* c */}</div>', errors: [{ messageId: 'comment' }] },
    { code: 'const view = <div>{/* c */ x}</div>', errors: [{ messageId: 'comment' }] },
    { code: 'const view = <>{x /* trailing */}</>', errors: [{ messageId: 'comment' }] },
    { code: 'const view = (\n  <div\n    // why\n    id="a"\n  />\n)', errors: [{ messageId: 'comment' }] },
    { code: 'const view = <div onClick={() => { /* c */ }} />', errors: [{ messageId: 'comment' }] },
    { code: 'const view = <div>{}</div>', errors: [{ messageId: 'empty' }] },
  ],
})
