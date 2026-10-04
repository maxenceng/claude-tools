import { afterAll, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import { DEFAULT_LANGUAGE, i18n } from '../i18n/i18n'
import { server } from './server'

// Node's Request rejects relative URLs, but the client's baseUrl is '/' (same-origin in
// the browser). Resolve them against the jsdom origin, as a browser would.
const NodeRequest = globalThis.Request
globalThis.Request = class extends NodeRequest {
  constructor(input: RequestInfo | URL, init?: RequestInit) {
    super(typeof input === 'string' ? new URL(input, window.location.href).href : input, init)
  }
}

// Listening at module level, not in beforeAll: openapi-fetch captures globalThis.fetch when
// the client module is created, which happens while the test file is imported, before any
// beforeAll hook runs. Patched late, the client would keep the unpatched fetch.
server.listen({ onUnhandledFrame: 'error' })

// Tests assert English copy, whatever language the machine running them speaks.
await i18n.changeLanguage(DEFAULT_LANGUAGE)

afterEach(async () => {
  server.resetHandlers()
  cleanup()
  await i18n.changeLanguage(DEFAULT_LANGUAGE)
})
afterAll(() => {
  server.close()
})
