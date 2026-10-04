import { describe, expect, it } from 'vitest'
import { pickLanguage } from './i18n'

describe('pickLanguage', () => {
  it.each([
    ['fr-CA', 'fr'],
    ['fr', 'fr'],
    ['en-GB', 'en'],
    ['de-DE', 'en'],
    ['', 'en'],
  ])('picks %j as %j', (browser, picked) => {
    expect(pickLanguage(browser)).toBe(picked)
  })
})
