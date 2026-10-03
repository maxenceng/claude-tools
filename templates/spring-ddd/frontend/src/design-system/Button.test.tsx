import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Button } from './Button'

describe('Button', () => {
  it.each(['button', 'submit'] as const)('renders the %s type it is given', (type) => {
    render(<Button type={type}>Go</Button>)

    expect(screen.getByRole('button', { name: 'Go' }).getAttribute('type')).toBe(type)
  })

  it('calls onClick when pressed', () => {
    const onClick = vi.fn()
    render(
      <Button type="button" variant="link" onClick={onClick}>
        Retry
      </Button>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))

    expect(onClick).toHaveBeenCalledOnce()
  })
})
