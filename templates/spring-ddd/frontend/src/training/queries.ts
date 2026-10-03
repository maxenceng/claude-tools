import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { ApiError, unwrap } from '../api/problem'

export const trainingKeys = {
  all: ['training'] as const,
  popularity: (title: string) => [...trainingKeys.all, 'popularity', title] as const,
}

export function useCoursePopularity(title: string) {
  return useQuery({
    queryKey: trainingKeys.popularity(title),
    queryFn: async () =>
      unwrap(await api.GET('/api/courses/popularity', { params: { query: { title } } })),
    enabled: title.trim() !== '',
    // The server answered, so the UI offers Retry; only a network failure is retried silently.
    retry: (failures, error) => !(error instanceof ApiError) && failures < 1,
  })
}
