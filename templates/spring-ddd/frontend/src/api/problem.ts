export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

type Result<T> = { data?: T; error?: unknown; response: Response }

/** The data of a successful call; a failed one becomes an ApiError carrying the ProblemDetail. */
export function unwrap<T>({ data, error, response }: Result<T>): T {
  if (!response.ok) {
    const detail =
      typeof error === 'object' && error !== null && 'detail' in error && typeof error.detail === 'string'
        ? error.detail
        : response.statusText
    throw new ApiError(response.status, detail)
  }
  // A success with no body (204) has no data, so a no-content route's caller gets undefined.
  return data as T
}
