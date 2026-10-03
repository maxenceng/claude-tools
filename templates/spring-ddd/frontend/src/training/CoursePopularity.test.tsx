import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { delay, http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { i18n } from '../i18n/i18n'
import { server } from '../test/server'
import { CoursePopularity } from './CoursePopularity'

type Responder = (info: { request: Request }) => Response | Promise<Response>

function popularity(respond: Responder): void {
  server.use(http.get('*/api/courses/popularity', respond))
}

function problem(status: number, detail: string): () => Response {
  return () => HttpResponse.json({ status, detail }, { status })
}

function renderScreen(): void {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <CoursePopularity />
    </QueryClientProvider>,
  )
}

function ask(title: string): void {
  renderScreen()
  fireEvent.change(screen.getByLabelText('Course title'), { target: { value: title } })
  fireEvent.click(screen.getByRole('button', { name: 'Look up' }))
}

describe('CoursePopularity', () => {
  it('asks nothing until a title is submitted', async () => {
    let calls = 0
    popularity(() => {
      calls += 1
      return HttpResponse.json({ title: 'DDD', popularity: 73 })
    })
    renderScreen()

    fireEvent.change(screen.getByLabelText('Course title'), { target: { value: 'DDD' } })
    await delay(50)

    expect(calls).toBe(0)
    expect(screen.queryByRole('status')).toBeNull()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('shows the popularity of a known course', async () => {
    let asked: string | null = null
    popularity(({ request }) => {
      asked = new URL(request.url).searchParams.get('title')
      return HttpResponse.json({ title: 'DDD', popularity: 73 })
    })

    ask('DDD')

    expect(await screen.findByText('73')).toBeTruthy()
    expect(asked).toBe('DDD')
  })

  it('says, neutrally, that a course has no popularity yet', async () => {
    popularity(problem(404, 'no popularity'))

    ask('Brand new')

    expect(await screen.findByText(/no popularity yet/i)).toBeTruthy()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('offers a retry when the vendor is unavailable', async () => {
    let calls = 0
    popularity(() => {
      calls += 1
      return problem(503, 'vendor down')()
    })

    ask('DDD')
    const alert = await screen.findByRole('alert')
    expect(calls).toBe(1)
    expect(alert.textContent).toContain('vendor down')

    popularity(() => HttpResponse.json({ title: 'DDD', popularity: 41 }))
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))

    expect(await screen.findByText('41')).toBeTruthy()
  })

  it('says the server could not be reached when nothing answers, not what fetch threw', async () => {
    popularity(() => HttpResponse.error())

    ask('DDD')

    const alert = await screen.findByRole('alert', {}, { timeout: 3000 })
    expect(alert.textContent).toContain('The server could not be reached; try again.')
  })

  it('ties a rejected title to the input, without an alert', async () => {
    popularity(problem(400, 'title must not be blank'))

    ask('x')

    const message = await screen.findByText('title must not be blank')
    const input = screen.getByLabelText('Course title')
    expect(input.getAttribute('aria-describedby')).toBe(message.id)
    expect(input.getAttribute('aria-invalid')).toBe('true')
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('announces a rejected title submitted with Enter from the input', async () => {
    popularity(problem(400, 'title must not be blank'))
    renderScreen()
    const input = screen.getByLabelText<HTMLInputElement>('Course title')
    const regions = Array.from(document.querySelectorAll('[aria-live="polite"]'))

    input.focus()
    fireEvent.change(input, { target: { value: 'x' } })
    fireEvent.submit(input.form!)

    const message = await screen.findByText('title must not be blank')
    expect(regions.some((region) => region.contains(message))).toBe(true)
  })

  it('shows a busy indicator while the lookup is in flight', async () => {
    popularity(async () => {
      await delay(50)
      return HttpResponse.json({ title: 'DDD', popularity: 73 })
    })

    ask('DDD')

    expect((await screen.findByRole('status')).textContent).toMatch(/looking up/i)
    expect(await screen.findByText('73')).toBeTruthy()
  })

  it('shows the busy indicator again, then the new value, on a second lookup', async () => {
    popularity(() => HttpResponse.json({ title: 'DDD', popularity: 73 }))
    ask('DDD')
    expect(await screen.findByText('73')).toBeTruthy()

    popularity(async () => {
      await delay(50)
      return HttpResponse.json({ title: 'CQRS', popularity: 12 })
    })
    fireEvent.change(screen.getByLabelText('Course title'), { target: { value: 'CQRS' } })
    fireEvent.click(screen.getByRole('button', { name: 'Look up' }))

    expect((await screen.findByRole('status')).textContent).toMatch(/looking up/i)
    expect(await screen.findByText('12')).toBeTruthy()
    expect(screen.queryByText('73')).toBeNull()
  })

  it('speaks French when the language is French', async () => {
    await i18n.changeLanguage('fr')

    renderScreen()

    expect(screen.getByRole('button', { name: 'Rechercher' })).toBeTruthy()
  })
})
