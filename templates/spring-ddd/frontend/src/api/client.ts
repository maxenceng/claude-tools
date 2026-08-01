import createClient from 'openapi-fetch'
import type { paths } from './generated/schema'

/**
 * The only way this application talks to the backend.
 *
 * Types come from the OpenAPI schema, so an API change surfaces as a compile error
 * rather than as a runtime surprise — but only once the schema has been recaptured.
 * That is two steps, not one, and skipping the first is how the client silently drifts:
 *
 *   make run              # in another shell, the schema is read from the live app
 *   make openapi          # writes docs/openapi.json
 *   make openapi-client   # writes src/api/generated/schema.d.ts
 *
 * Never hand-edit the generated file; it is overwritten.
 */
export const api = createClient<paths>({ baseUrl: '/' })
