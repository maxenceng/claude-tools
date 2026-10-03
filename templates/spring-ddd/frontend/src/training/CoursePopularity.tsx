import { useState, type FormEvent } from 'react'
import { ApiError } from '../api/problem'
import { useCoursePopularity } from './queries'

export function CoursePopularity() {
  const [draft, setDraft] = useState('')
  const [submitted, setSubmitted] = useState('')
  const popularity = useCoursePopularity(submitted)
  const error = popularity.error instanceof ApiError ? popularity.error : null
  const rejected = error?.status === 400 ? error.detail : null

  function submit(event: FormEvent) {
    event.preventDefault()
    setSubmitted(draft)
  }

  return (
    <section className="mt-8" aria-labelledby="popularity-heading">
      <h2 id="popularity-heading" className="text-lg font-medium">
        Course popularity
      </h2>
      <form onSubmit={submit} className="mt-3 flex items-start gap-3">
        <div className="flex-1">
          <label htmlFor="course-title" className="block text-sm font-medium">
            Course title
          </label>
          <input
            id="course-title"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            aria-invalid={rejected !== null}
            aria-describedby={rejected !== null ? 'course-title-error' : undefined}
            className="mt-1 w-full rounded border border-neutral-300 px-3 py-2"
          />
          {rejected !== null && (
            <p id="course-title-error" className="mt-1 text-sm text-red-700">
              {rejected}
            </p>
          )}
        </div>
        <button type="submit" className="mt-6 rounded bg-neutral-900 px-4 py-2 text-white">
          Look up
        </button>
      </form>
      <Outcome popularity={popularity} />
    </section>
  )
}

function Outcome({ popularity }: { popularity: ReturnType<typeof useCoursePopularity> }) {
  if (popularity.isPending) {
    return popularity.fetchStatus === 'fetching' ? (
      <p role="status" className="mt-4 text-sm text-neutral-600">
        Looking up…
      </p>
    ) : null
  }
  if (popularity.isError) {
    const status = popularity.error instanceof ApiError ? popularity.error.status : undefined
    if (status === 400) return null
    if (status === 404) {
      return <p className="mt-4 text-sm text-neutral-600">No popularity yet for this course.</p>
    }
    return (
      <div role="alert" className="mt-4 text-sm text-red-700">
        <p>{popularity.error.message}</p>
        <button type="button" onClick={() => popularity.refetch()} className="mt-2 underline">
          Retry
        </button>
      </div>
    )
  }
  return (
    <p className="mt-4" aria-busy={popularity.isFetching}>
      <span className="text-4xl font-semibold tabular-nums">{popularity.data.popularity}</span>
      <span className="ml-2 text-sm text-neutral-600">popularity of {popularity.data.title}</span>
    </p>
  )
}
