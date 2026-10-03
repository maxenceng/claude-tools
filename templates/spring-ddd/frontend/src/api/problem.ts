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
  if (error !== undefined || data === undefined) {
    const detail =
      typeof error === 'object' && error !== null && 'detail' in error && typeof error.detail === 'string'
        ? error.detail
        : response.statusText
    throw new ApiError(response.status, detail)
  }
  return data
}
