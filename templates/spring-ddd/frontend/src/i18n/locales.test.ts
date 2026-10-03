import { describe, expect, it } from 'vitest'
import { resources } from './i18n'

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

const namespaces = Object.keys(resources.en) as (keyof typeof resources.en)[]

describe('locales', () => {
  it('cover the same namespaces in every language', () => {
    expect(Object.keys(resources.fr).sort()).toEqual([...namespaces].sort())
  })

  it.each(namespaces)('give %s the same keys in English and French', (namespace) => {
    const english = [...leaves(resources.en[namespace]).keys()].sort()
    const french = [...leaves(resources.fr[namespace]).keys()].sort()

    expect(french).toEqual(english)
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
