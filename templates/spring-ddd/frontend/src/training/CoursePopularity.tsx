import { useId, useState, type FormEvent, type JSX } from 'react'
import { useTranslation } from 'react-i18next'
import { detailOf, isNotFound, isRejected, rejectionOf } from '../api/problem'
import { Alert, Button, Heading, Stack, Status, Text, TextField } from '../design-system'
import { useCoursePopularity } from './queries'

type Popularity = ReturnType<typeof useCoursePopularity>

/**
 * Looks up how popular a course is, by title.
 *
 * A lookup runs per submitted title, not per keystroke. A title the server rejects (400)
 * is shown on the field, through TextField's live error slot, so it is heard whether the
 * form was submitted by Enter or by the button. Every other outcome renders in a polite
 * live region below the form.
 */
export function CoursePopularity(): JSX.Element {
  const { t } = useTranslation('training')
  const headingId = useId()
  const [draft, setDraft] = useState('')
  const [submitted, setSubmitted] = useState('')
  const popularity = useCoursePopularity(submitted)
  const rejected = rejectionOf(popularity.error)

  function submit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault()
    setSubmitted(draft)
  }

  return (
    <section aria-labelledby={headingId}>
      <Stack gap="md">
        <Heading level={2} id={headingId}>
          {t('popularity.heading')}
        </Heading>
        <form onSubmit={submit}>
          <Stack gap="sm">
            <TextField label={t('popularity.titleLabel')} value={draft} onChange={setDraft} error={rejected} />
            <Stack direction="horizontal" gap="sm">
              <Button type="submit">{t('popularity.lookUp')}</Button>
            </Stack>
          </Stack>
        </form>
        <div aria-live="polite">
          <Outcome popularity={popularity} />
        </div>
      </Stack>
    </section>
  )
}

interface OutcomeProps {
  popularity: Popularity
}

/**
 * What the last lookup came to. Nothing while idle, and nothing for a 400, which
 * CoursePopularity shows on the field instead. A 404 is a neutral answer, not a failure;
 * anything else is, and offers Retry.
 */
function Outcome({ popularity }: OutcomeProps): JSX.Element | null {
  const { t } = useTranslation('training')

  if (popularity.isLoading) return <Status>{t('popularity.lookingUp')}</Status>
  if (popularity.isPending) return null
  if (popularity.isError) {
    if (isRejected(popularity.error)) return null
    if (isNotFound(popularity.error)) {
      return (
        <Text tone="muted" size="sm">
          {t('popularity.notFound')}
        </Text>
      )
    }
    return (
      <Alert>
        <Text>{detailOf(popularity.error) ?? t('popularity.unreachable')}</Text>
        <Button type="button" variant="link" onClick={() => void popularity.refetch()}>
          {t('popularity.retry')}
        </Button>
      </Alert>
    )
  }
  return (
    <Stack direction="horizontal" gap="sm" align="baseline">
      <Text as="span" size="display">
        {popularity.data.popularity}
      </Text>
      <Text as="span" tone="muted" size="sm">
        {t('popularity.popularityOf', { title: popularity.data.title })}
      </Text>
    </Stack>
  )
}
