import { describe, expect, it } from 'vitest'
import { ApiError, detailOf, HttpStatus, isAnswered, isNotFound, isRejected, rejectionOf, unwrap } from './problem'

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

describe('reading a failure', () => {
  const rejected = new ApiError(HttpStatus.BAD_REQUEST, 'title must not be blank')
  const notFound = new ApiError(HttpStatus.NOT_FOUND, 'no popularity')
  const unavailable = new ApiError(503, 'vendor down')
  const unanswered = new TypeError('Failed to fetch')

  it('tells an answer from a request nothing answered', () => {
    expect(isAnswered(unavailable)).toBe(true)
    expect(isAnswered(unanswered)).toBe(false)
    expect(isAnswered(null)).toBe(false)
  })

  it('recognises a rejected input only by its 400', () => {
    expect(isRejected(rejected)).toBe(true)
    expect([notFound, unavailable, unanswered, null].some(isRejected)).toBe(false)
  })

  it('recognises nothing-at-that-address only by its 404', () => {
    expect(isNotFound(notFound)).toBe(true)
    expect([rejected, unavailable, unanswered, null].some(isNotFound)).toBe(false)
  })

  it('gives the reason for a rejection, and nothing for any other failure', () => {
    expect(rejectionOf(rejected)).toBe('title must not be blank')
    expect([notFound, unavailable, unanswered, null].map(rejectionOf)).toEqual([undefined, undefined, undefined, undefined])
  })

  it('gives what the server said, and nothing when it said nothing', () => {
    expect(detailOf(unavailable)).toBe('vendor down')
    expect(detailOf(unanswered)).toBeUndefined()
  })
})
