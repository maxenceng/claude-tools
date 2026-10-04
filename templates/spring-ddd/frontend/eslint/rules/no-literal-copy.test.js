import { typedRuleTester } from './rule-tester.js'
import rule from './no-literal-copy.js'

const prelude = `
import type { ReactNode } from 'react'
declare function t(key: string): string
declare const on: boolean
declare const detail: string | undefined
declare const name: string
declare const count: number
function Text(props: { children?: ReactNode; tone?: 'default' | 'muted' }) { return <p>{props.children}</p> }
function Field(props: { label: string; value: string; type: 'button' | 'submit' }) { return <input value={props.value} type={props.type} /> }
`
const view = (jsx) => `${prelude}\nexport const view = ${jsx}\n`
const copy = (count) => Array.from({ length: count }, () => ({ messageId: 'copy' }))
const copyInProp = (count) => Array.from({ length: count }, () => ({ messageId: 'copyInProp' }))

typedRuleTester().run('no-literal-copy', rule, {
  valid: [
    view(`<Text tone="muted">{t('popularity.heading')}</Text>`),
    view(`<Field label={t('popularity.titleLabel')} value="" type="submit" />`),
    view(`<Text key="row">{count}</Text>`),
    view(`<Text>{on ? t('a') : t('b')}</Text>`),
    view(`<Text>{detail ?? t('popularity.unreachable')}</Text>`),
    view('<Text>{`${name}${count}`}</Text>'),
    view(`<Text>{' '}</Text>`),
    view(`<div id="x" role="status" aria-live="polite" data-state="open" className="c" />`),
    view(`<a href="/courses" target="_blank" rel="noreferrer" aria-current="page">{t('k')}</a>`),
    view(`<svg viewBox="0 0 1 1" aria-hidden="true"><path d="M0 0" fill="none" /></svg>`),
    view(`<input type="number" min="0" max="9" step="1" pattern="[0-9]+" lang="fr" />`),
  ],
  invalid: [
    { code: view(`<Text>Course popularity</Text>`), errors: copy(1) },
    { code: view(`<Text>{detail ?? 'Something went wrong'}</Text>`), errors: copy(1) },
    { code: view(`<Text>{on ? 'x' : t('y')}</Text>`), errors: copy(1) },
    { code: view(`<Text>{on && 'Ready'}</Text>`), errors: copy(1) },
    { code: view(`<Field label={on ? 'Yes' : 'No'} value="" type="submit" />`), errors: copyInProp(2) },
    { code: view(`<Text>{'x' as string}</Text>`), errors: copy(1) },
    { code: view(`<Field label={'x' satisfies string} value="" type="button" />`), errors: copyInProp(1) },
    { code: view('<Text>{`Hello ${name}`}</Text>'), errors: copy(1) },
    { code: view(`<Text>{'Hello ' + name}</Text>`), errors: copy(1) },
    { code: view(`<Field label="Course title" value="" type="submit" />`), errors: copyInProp(1) },
    { code: view(`<Text children="Hi" />`), errors: copyInProp(1) },
    { code: view(`<img alt="A cat" src="/cat.png" />`), errors: copy(1) },
    { code: view(`<input placeholder="Search" aria-label={on ? 'Find' : t('k')} />`), errors: copy(2) },
    { code: view(`<abbr title="Domain-driven design">{t('k')}</abbr>`), errors: copy(1) },
  ],
})
