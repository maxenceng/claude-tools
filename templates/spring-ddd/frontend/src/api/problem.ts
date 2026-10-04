export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

/** The statuses the client answers differently from any other failure. */
export const HttpStatus = {
  BAD_REQUEST: 400,
  NOT_FOUND: 404,
} as const

/** Whether the server answered, as opposed to the request never reaching it. */
export function isAnswered(error: unknown): error is ApiError {
  return error instanceof ApiError
}

/** Whether the server refused the request's input (400). */
export function isRejected(error: unknown): error is ApiError {
  return isAnswered(error) && error.status === HttpStatus.BAD_REQUEST
}

/** Whether the server has nothing at that address (404) — an answer, not a failure. */
export function isNotFound(error: unknown): boolean {
  return isAnswered(error) && error.status === HttpStatus.NOT_FOUND
}

/** Why the server refused the request's input, or undefined when it did not refuse it. */
export function rejectionOf(error: unknown): string | undefined {
  return isRejected(error) ? error.detail : undefined
}

/** What the server said went wrong, or undefined when nothing answered. */
export function detailOf(error: unknown): string | undefined {
  return isAnswered(error) ? error.detail : undefined
}

interface Result<T> {
  data?: T
  error?: unknown
  response: Response
}

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
