import { describe, expect, it } from 'vitest'
import { ApiError } from '../api/problem'
import { isAskable, NETWORK_RETRIES, retriesOnlyUnansweredRequests } from './queries'

describe('isAskable', () => {
  it.each(['', '   ', '\t'])('does not ask about the blank title %j', (title) => {
    expect(isAskable(title)).toBe(false)
  })

  it('asks about a title with content', () => {
    expect(isAskable(' DDD ')).toBe(true)
  })
})

describe('retriesOnlyUnansweredRequests', () => {
  it('never retries a request the server answered', () => {
    expect(retriesOnlyUnansweredRequests(0, new ApiError(503, 'vendor down'))).toBe(false)
  })

  it('retries a network failure until the retry budget is spent', () => {
    const networkFailure = new TypeError('Failed to fetch')

    expect(retriesOnlyUnansweredRequests(NETWORK_RETRIES - 1, networkFailure)).toBe(true)
    expect(retriesOnlyUnansweredRequests(NETWORK_RETRIES, networkFailure)).toBe(false)
  })
})
