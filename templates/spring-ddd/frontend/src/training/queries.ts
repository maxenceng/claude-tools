import { useQuery, type UseQueryResult } from '@tanstack/react-query'
import { api, type Schema } from '../api/client'
import { ApiError, unwrap } from '../api/problem'

/** A network failure is retried once, silently, before the screen offers Retry. */
export const NETWORK_RETRIES = 1

/**
 * Query keys for this context, built in one place so they cannot drift.
 *
 * `as const` makes each key a readonly tuple, so a key cannot be mutated after it is
 * built and invalidating by prefix (`trainingKeys.all`) stays type-checked — TanStack
 * Query's documented key-factory pattern.
 */
export const trainingKeys = {
  all: ['training'] as const,
  popularity: (title: string) => [...trainingKeys.all, 'popularity', title] as const,
}

/** Whether a title is worth asking about; a blank one is not sent at all. */
export function isAskable(title: string): boolean {
  return title.trim() !== ''
}

/**
 * Retries only a request nobody answered. When the server answered (an ApiError), the
 * answer stands and the screen offers Retry instead.
 */
export function retriesOnlyUnansweredRequests(failureCount: number, error: Error): boolean {
  return !(error instanceof ApiError) && failureCount < NETWORK_RETRIES
}

export function useCoursePopularity(title: string): UseQueryResult<Schema<'CoursePopularityResponse'>> {
  return useQuery({
    queryKey: trainingKeys.popularity(title),
    queryFn: async () =>
      unwrap(await api.GET('/api/courses/popularity', { params: { query: { title } } })),
    enabled: isAskable(title),
    retry: retriesOnlyUnansweredRequests,
  })
}
