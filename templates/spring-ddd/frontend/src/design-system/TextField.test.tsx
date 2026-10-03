import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { TextField } from './TextField'

const noop = (): void => {}

describe('TextField', () => {
  it('labels its input', () => {
    render(<TextField label="Course title" value="DDD" onChange={noop} />)

    expect(screen.getByLabelText<HTMLInputElement>('Course title').value).toBe('DDD')
  })

  it('hands the typed value to onChange', () => {
    const onChange = vi.fn()
    render(<TextField label="Course title" value="" onChange={onChange} />)

    fireEvent.change(screen.getByLabelText('Course title'), { target: { value: 'CQRS' } })

    expect(onChange).toHaveBeenCalledWith('CQRS')
  })

  it('is neither invalid nor described while there is no error', () => {
    render(<TextField label="Course title" value="" onChange={noop} />)
    const input = screen.getByLabelText('Course title')

    expect(input.getAttribute('aria-invalid')).toBeNull()
    expect(input.getAttribute('aria-describedby')).toBeNull()
  })

  it('announces an error in a live region that existed before the error', () => {
    const { rerender } = render(<TextField label="Course title" value="x" onChange={noop} />)
    const regions = Array.from(document.querySelectorAll('[aria-live="polite"]'))

    rerender(<TextField label="Course title" value="x" onChange={noop} error="title must not be blank" />)

    const message = screen.getByText('title must not be blank')
    expect(regions.some((region) => region.contains(message))).toBe(true)
  })

  it('marks the input invalid and described by the error', () => {
    render(<TextField label="Course title" value="x" onChange={noop} error="title must not be blank" />)
    const input = screen.getByLabelText('Course title')

    expect(input.getAttribute('aria-invalid')).toBe('true')
    expect(input.getAttribute('aria-describedby')).toBe(screen.getByText('title must not be blank').id)
  })
})
