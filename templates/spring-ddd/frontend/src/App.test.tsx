import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'

/**
 * A smoke test, and deliberately a weak one — it exists so the suite is green from the
 * first commit and so the testing setup itself is proven to work. Delete it once there
 * is a real screen to test; a permanent test that only asserts a heading renders will
 * outlive its usefulness and still cost a run every time.
 */
describe('App', () => {
  it('renders', () => {
    render(<App />)

    expect(screen.getByRole('heading')).toBeTruthy()
  })
})
