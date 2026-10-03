import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import enCommon from './locales/en/common.json'
import enTraining from './locales/en/training.json'
import frCommon from './locales/fr/common.json'
import frTraining from './locales/fr/training.json'

export const DEFAULT_LANGUAGE = 'en'
export const SUPPORTED_LANGUAGES = ['en', 'fr'] as const
export type Language = (typeof SUPPORTED_LANGUAGES)[number]

/** One namespace per bounded context, plus `common` for the application shell. */
export const resources = {
  en: { common: enCommon, training: enTraining },
  fr: { common: frCommon, training: frTraining },
} as const

function isSupported(language: string): language is Language {
  return (SUPPORTED_LANGUAGES as readonly string[]).includes(language)
}

/** The browser's language when this application speaks it (`fr-CA` → `fr`), else the default. */
export function pickLanguage(browserLanguage: string): Language {
  const base = browserLanguage.split('-')[0]?.toLowerCase() ?? ''
  return isSupported(base) ? base : DEFAULT_LANGUAGE
}

i18n.on('languageChanged', (language) => {
  document.documentElement.lang = language
})

void i18n.use(initReactI18next).init({
  resources,
  lng: pickLanguage(navigator.language),
  fallbackLng: DEFAULT_LANGUAGE,
  supportedLngs: SUPPORTED_LANGUAGES,
  defaultNS: 'common',
  ns: Object.keys(resources.en),
  // Resources are bundled, so initialisation completes before the first render.
  initAsync: false,
  // React escapes what it renders; escaping here too would double-escape.
  interpolation: { escapeValue: false },
  returnNull: false,
})

export { i18n }
