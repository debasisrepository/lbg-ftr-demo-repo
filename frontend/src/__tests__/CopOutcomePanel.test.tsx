import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CopOutcomePanel } from '../components/payees/CopOutcomePanel'
import { CopCheckOut } from '../features/payees/usePayees'

describe('CopOutcomePanel', () => {
  it('should render match outcome', () => {
    const copCheck: CopCheckOut = {
      cop_check_id: 'cop-1',
      outcome: 'match',
      suggested_name: null,
      policy_treatment: 'allow',
      checked_at: '2024-01-01T10:00:00Z',
      expires_at: null,
      customer_acknowledged_at: null,
    }

    render(<CopOutcomePanel copCheck={copCheck} />)

    expect(screen.getByText('Name matches')).toBeInTheDocument()
    expect(screen.getByText(/We checked the name against the account/)).toBeInTheDocument()
  })

  it('should render mismatch outcome with warning', () => {
    const copCheck: CopCheckOut = {
      cop_check_id: 'cop-1',
      outcome: 'mismatch',
      suggested_name: 'Correct Name',
      policy_treatment: 'warn',
      checked_at: '2024-01-01T10:00:00Z',
      expires_at: null,
      customer_acknowledged_at: null,
    }

    render(<CopOutcomePanel copCheck={copCheck} />)

    expect(screen.getByText(/the name doesn't match/)).toBeInTheDocument()
    expect(screen.getByText(/Paying the wrong account could mean/)).toBeInTheDocument()
  })

  it('should render partial_match outcome', () => {
    const copCheck: CopCheckOut = {
      cop_check_id: 'cop-1',
      outcome: 'partial_match',
      suggested_name: 'Similar Name',
      policy_treatment: 'warn',
      checked_at: '2024-01-01T10:00:00Z',
      expires_at: null,
      customer_acknowledged_at: null,
    }

    render(<CopOutcomePanel copCheck={copCheck} />)

    expect(screen.getByText(/the name doesn't match/)).toBeInTheDocument()
  })

  it('should render unavailable outcome', () => {
    const copCheck: CopCheckOut = {
      cop_check_id: 'cop-1',
      outcome: 'unavailable',
      suggested_name: null,
      policy_treatment: 'warn',
      checked_at: '2024-01-01T10:00:00Z',
      expires_at: null,
      customer_acknowledged_at: null,
    }

    render(<CopOutcomePanel copCheck={copCheck} />)

    expect(screen.getByText(/We couldn't check this payee/)).toBeInTheDocument()
  })

  it('should show acknowledge button for warn treatment', async () => {
    const user = userEvent.setup()
    const handleAcknowledge = vi.fn()
    const copCheck: CopCheckOut = {
      cop_check_id: 'cop-1',
      outcome: 'mismatch',
      suggested_name: null,
      policy_treatment: 'warn',
      checked_at: '2024-01-01T10:00:00Z',
      expires_at: null,
      customer_acknowledged_at: null,
    }

    render(<CopOutcomePanel copCheck={copCheck} onAcknowledge={handleAcknowledge} />)

    const button = screen.getByText('I understand, continue')
    await user.click(button)

    expect(handleAcknowledge).toHaveBeenCalled()
  })

  it('should not show acknowledge button for block treatment', () => {
    const copCheck: CopCheckOut = {
      cop_check_id: 'cop-1',
      outcome: 'mismatch',
      suggested_name: null,
      policy_treatment: 'block',
      checked_at: '2024-01-01T10:00:00Z',
      expires_at: null,
      customer_acknowledged_at: null,
    }

    render(<CopOutcomePanel copCheck={copCheck} />)

    expect(screen.queryByText('I understand, continue')).not.toBeInTheDocument()
  })
})
