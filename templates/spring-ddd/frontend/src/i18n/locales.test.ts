import { describe, expect, it } from 'vitest'
import { resources, SUPPORTED_LANGUAGES } from './i18n'

/** Every leaf of a translation file as `dotted.key` → value. */
function leaves(tree: object, prefix = ''): Map<string, unknown> {
  return new Map(
    Object.entries(tree).flatMap(([key, value]) => {
      const path = prefix === '' ? key : `${prefix}.${key}`
      return typeof value === 'object' && value !== null
        ? [...leaves(value as object, path)]
        : [[path, value] as const]
    }),
  )
}

const PLURAL_SUFFIX = /_(?<form>zero|one|two|few|many|other)$/

/** The plural forms a language's grammar has; i18next looks each one up as a key suffix. */
function pluralForms(language: string): string[] {
  return new Intl.PluralRules(language).resolvedOptions().pluralCategories
}

/** The keys with their plural suffix removed, so `count_one` and `count_many` are both `count`. */
function baseKeys(keys: string[]): string[] {
  return [...new Set(keys.map((key) => key.replace(PLURAL_SUFFIX, '')))].sort()
}

/**
 * Each plural key whose forms are not exactly its language's. `_zero` is optional anywhere:
 * i18next tries it for a count of 0 whatever the language's grammar.
 */
function pluralMismatches(keys: string[], language: string): string[] {
  const expected = [...pluralForms(language)].sort().join()
  const formsByBase = new Map<string, string[]>()
  for (const key of keys) {
    const form = PLURAL_SUFFIX.exec(key)?.groups?.form
    if (form !== undefined && form !== 'zero') {
      const base = key.replace(PLURAL_SUFFIX, '')
      formsByBase.set(base, [...(formsByBase.get(base) ?? []), form])
    }
  }
  return [...formsByBase]
    .filter(([, forms]) => [...forms].sort().join() !== expected)
    .map(([base]) => `${language}:${base}`)
}

const namespaces = Object.keys(resources.en) as (keyof typeof resources.en)[]

describe('plural forms', () => {
  it('are the ones each language has', () => {
    expect(pluralForms('en')).toEqual(['one', 'other'])
    expect(pluralForms('fr')).toEqual(['one', 'many', 'other'])
  })

  it('pass when a key has exactly its language forms', () => {
    expect(pluralMismatches(['count_one', 'count_other', 'title'], 'en')).toEqual([])
    expect(pluralMismatches(['count_one', 'count_many', 'count_other'], 'fr')).toEqual([])
  })

  it('pass with an extra zero form in any language', () => {
    expect(pluralMismatches(['count_zero', 'count_one', 'count_other'], 'en')).toEqual([])
  })

  it('fail when a key misses a form, or has one its language lacks', () => {
    expect(pluralMismatches(['count_one', 'count_other'], 'fr')).toEqual(['fr:count'])
    expect(pluralMismatches(['count_one', 'count_many', 'count_other'], 'en')).toEqual(['en:count'])
  })

  it('do not count as different keys between languages', () => {
    expect(baseKeys(['count_one', 'count_many', 'count_other', 'title'])).toEqual(
      baseKeys(['count_one', 'count_other', 'title']),
    )
  })
})

describe('locales', () => {
  it('cover the same namespaces in every language', () => {
    expect(Object.keys(resources.fr).sort()).toEqual([...namespaces].sort())
  })

  it.each(namespaces)('give %s the same keys in English and French, plural forms aside', (namespace) => {
    const english = baseKeys([...leaves(resources.en[namespace]).keys()])
    const french = baseKeys([...leaves(resources.fr[namespace]).keys()])

    expect(french).toEqual(english)
  })

  it.each(namespaces)('give each %s plural exactly the forms its language has', (namespace) => {
    const mismatches = SUPPORTED_LANGUAGES.flatMap((language) =>
      pluralMismatches([...leaves(resources[language][namespace]).keys()], language),
    )

    expect(mismatches).toEqual([])
  })

  it.each(namespaces)('leave no %s message empty', (namespace) => {
    const empty = (['en', 'fr'] as const).flatMap((language) =>
      [...leaves(resources[language][namespace])]
        .filter(([, value]) => typeof value !== 'string' || value.trim() === '')
        .map(([key]) => `${language}/${namespace}:${key}`),
    )

    expect(empty).toEqual([])
  })
})
