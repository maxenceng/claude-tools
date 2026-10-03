import { keepPreviousData, useQuery } from '@tanstack/react-query'
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
    retry: (failures, error) => !(error instanceof ApiError && error.status < 500) && failures < 1,
    placeholderData: keepPreviousData,
  })
}
