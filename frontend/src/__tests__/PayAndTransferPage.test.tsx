import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { PayAndTransferPage } from '../pages/PayAndTransferPage'
import * as payeesHook from '../features/payees/usePayees'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../features/payees/usePayees')

describe('PayAndTransferPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockPayees = [
    {
      payee_id: 'payee-1',
      customer_id: 'cust-1',
      profile_id: 'profile-1',
      payee_name: 'Jamie Clarke',
      sort_code: '04-00-04',
      account_number_masked: '****3746',
      payee_type: 'personal',
      is_saved: true,
      status: 'active',
      last_verified_at: null,
      latest_cop_check: null,
    },
    {
      payee_id: 'payee-2',
      customer_id: 'cust-1',
      profile_id: 'profile-1',
      payee_name: 'K Evans Lettings',
      sort_code: '20-45-77',
      account_number_masked: '****9842',
      payee_type: 'business',
      is_saved: true,
      status: 'active',
      last_verified_at: null,
      latest_cop_check: null,
    },
  ]

  it('should render loading state', () => {
    vi.spyOn(payeesHook, 'usePayees').mockReturnValue({
      payees: [],
      loading: true,
      error: null,
      refetch: vi.fn(),
    })

    render(
      <BrowserRouter>
        <PayAndTransferPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('should render error state', () => {
    vi.spyOn(payeesHook, 'usePayees').mockReturnValue({
      payees: [],
      loading: false,
      error: 'Failed to load payees',
      refetch: vi.fn(),
    })

    render(
      <BrowserRouter>
        <PayAndTransferPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/Failed to load payees/)).toBeInTheDocument()
  })

  it('should render payees list', async () => {
    vi.spyOn(payeesHook, 'usePayees').mockReturnValue({
      payees: mockPayees,
      loading: false,
      error: null,
      refetch: vi.fn(),
    })

    render(
      <BrowserRouter>
        <PayAndTransferPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 2, name: /Pay.*Transfer/i })).toBeInTheDocument()
    })

    expect(screen.getByText('Jamie Clarke')).toBeInTheDocument()
    expect(screen.getByText(/04-00-04.*3746/)).toBeInTheDocument()
    expect(screen.getByText('K Evans Lettings')).toBeInTheDocument()
    expect(screen.getByText(/20-45-77.*9842/)).toBeInTheDocument()
  })

  it('should navigate to add payee page', async () => {
    const user = userEvent.setup()
    vi.spyOn(payeesHook, 'usePayees').mockReturnValue({
      payees: mockPayees,
      loading: false,
      error: null,
      refetch: vi.fn(),
    })

    render(
      <BrowserRouter>
        <PayAndTransferPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 2, name: /Pay.*Transfer/i })).toBeInTheDocument()
    })

    const addButton = screen.getByText('Add a new payee')
    await user.click(addButton)

    expect(mockNavigate).toHaveBeenCalledWith('/add-payee')
  })

  it('should render move money section', async () => {
    vi.spyOn(payeesHook, 'usePayees').mockReturnValue({
      payees: mockPayees,
      loading: false,
      error: null,
      refetch: vi.fn(),
    })

    render(
      <BrowserRouter>
        <PayAndTransferPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Move money')).toBeInTheDocument()
    })

    expect(screen.getByText('Pay your credit card')).toBeInTheDocument()
    expect(screen.getByText('Balance £182.40')).toBeInTheDocument()
  })
})
