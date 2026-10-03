import { describe, expect, it } from 'vitest'
import { ApiError, unwrap } from './problem'

describe('unwrap', () => {
  it('returns the data of a successful call', () => {
    const data = { title: 'DDD', popularity: 73 }

    expect(unwrap({ data, response: new Response(null, { status: 200 }) })).toBe(data)
  })

  it('returns nothing, without throwing, for a successful call with no body', () => {
    expect(unwrap({ response: new Response(null, { status: 204 }) })).toBeUndefined()
  })

  it('turns a ProblemDetail into an ApiError with its status and detail', () => {
    const response = new Response(null, { status: 400 })

    expect(() => unwrap({ error: { detail: 'title must not be blank' }, response })).toThrow(
      expect.objectContaining({ name: 'ApiError', status: 400, detail: 'title must not be blank' }),
    )
    expect(() => unwrap({ error: { detail: 'x' }, response })).toThrow(ApiError)
  })

  it('falls back to the status text when the body has no detail', () => {
    const response = new Response(null, { status: 503, statusText: 'Service Unavailable' })

    expect(() => unwrap({ error: {}, response })).toThrow(
      expect.objectContaining({ status: 503, detail: 'Service Unavailable' }),
    )
  })
})
