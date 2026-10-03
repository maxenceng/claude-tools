import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Alert } from './Alert'
import { Heading } from './Heading'
import { Page } from './Page'
import { Stack } from './Stack'
import { Status } from './Status'
import { Text } from './Text'

describe('presentational primitives', () => {
  it('render their content with the semantics they promise', () => {
    render(
      <Page>
        <Stack gap="md">
          <Heading level={2}>Course popularity</Heading>
          <Text>No popularity yet.</Text>
          <Status>Looking up…</Status>
          <Alert>vendor down</Alert>
        </Stack>
      </Page>,
    )

    expect(screen.getByRole('main')).toBeTruthy()
    expect(screen.getByRole('heading', { level: 2, name: 'Course popularity' })).toBeTruthy()
    expect(screen.getByText('No popularity yet.').tagName).toBe('P')
    expect(screen.getByRole('status').textContent).toBe('Looking up…')
    expect(screen.getByRole('alert').textContent).toBe('vendor down')
  })
})
