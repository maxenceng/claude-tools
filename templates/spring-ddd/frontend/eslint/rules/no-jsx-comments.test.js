import { RuleTester } from 'eslint'
import rule from './no-jsx-comments.js'
import './rule-tester.js'

const tester = new RuleTester({
  languageOptions: { parserOptions: { ecmaFeatures: { jsx: true } } },
  linterOptions: { reportUnusedDisableDirectives: 'off' },
})

tester.run('no-jsx-comments', rule, {
  valid: [
    '// explains the view\nconst view = <div>{x}</div>',
    'const view = (\n  // explains the view\n  <div />\n)',
    '/* a */ const view = <><span id="a" /></>',
    'const view = (\n  <div>\n    {/* eslint-disable-next-line no-console -- why it is needed */}\n    <span id="a" />\n  </div>\n)',
    'const view = <div>{/* eslint-disable no-console */}{/* eslint-enable no-console */}</div>',
  ],
  invalid: [
    { code: 'const view = <div>{/* c */}</div>', errors: [{ messageId: 'comment' }] },
    { code: 'const view = <div>{/* c */ x}</div>', errors: [{ messageId: 'comment' }] },
    { code: 'const view = <>{x /* trailing */}</>', errors: [{ messageId: 'comment' }] },
    { code: 'const view = (\n  <div\n    // why\n    id="a"\n  />\n)', errors: [{ messageId: 'comment' }] },
    { code: 'const view = <div onClick={() => { /* c */ }} />', errors: [{ messageId: 'comment' }] },
    { code: 'const view = <div>{}</div>', errors: [{ messageId: 'empty' }] },
    { code: 'const view = <div>{/* eslint-enabled once the copy lands */}</div>', errors: [{ messageId: 'comment' }] },
    { code: 'const view = <div>{/* eslint-disabled for now */}</div>', errors: [{ messageId: 'comment' }] },
  ],
})
