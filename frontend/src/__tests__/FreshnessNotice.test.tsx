import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FreshnessNotice } from '../components/queue/FreshnessNotice'

describe('FreshnessNotice', () => {
  it('renders with data freshness timestamp', () => {
    const timestamp = '2026-11-24T07:42:00Z'
    render(<FreshnessNotice dataFreshness={timestamp} />)

    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.getByText(/Queue last refreshed/i)).toBeInTheDocument()
  })

  it('renders custom message when provided', () => {
    const timestamp = '2026-11-24T07:42:00Z'
    const customMessage = 'Refresh in progress...'
    render(<FreshnessNotice dataFreshness={timestamp} message={customMessage} />)

    expect(screen.getByText(customMessage)).toBeInTheDocument()
    expect(screen.queryByText(/Queue last refreshed/i)).not.toBeInTheDocument()
  })
})
