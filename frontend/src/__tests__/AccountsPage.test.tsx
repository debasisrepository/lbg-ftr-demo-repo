import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AccountsPage } from '../pages/AccountsPage'
import * as accountsHook from '../features/accounts/useAccountsOverview'
import * as profilesHook from '../features/accounts/useProfiles'

vi.mock('../features/accounts/useAccountsOverview')
vi.mock('../features/accounts/useProfiles')

describe('AccountsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockAccountsData = {
    accounts: [
      {
        bank_account_id: '1',
        external_account_ref: 'acc_001',
        account_type: 'current_account',
        account_name: 'Current Account',
        sort_code_masked: '12-34-56',
        account_number_masked: '****5678',
        currency_code: 'GBP',
        account_holder_name: 'Test User',
        current_balance_minor: 124836,
        available_balance_minor: 124836,
        overdraft_limit_minor: 100000,
        freshness_at: '2024-01-01T09:00:00Z',
        source_status: 'available',
        payment_permission: true,
      },
    ],
    loans: [],
    profile_id: 'profile-1',
    profile_display_name: 'Sasha Patel',
  }

  const mockProfiles = [
    {
      profile_id: 'profile-1',
      customer_id: 'cust-1',
      profile_type: 'personal',
      display_name: 'Personal',
      status: 'active',
      entitlements: [],
    },
  ]

  it('should render loading state', () => {
    vi.spyOn(accountsHook, 'useAccountsOverview').mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: vi.fn(),
    })
    vi.spyOn(profilesHook, 'useProfiles').mockReturnValue({
      profiles: [],
      loading: true,
      error: null,
      setActiveProfile: vi.fn(),
      refetch: vi.fn(),
    })

    render(
      <BrowserRouter>
        <AccountsPage />
      </BrowserRouter>
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('should render error state', () => {
    vi.spyOn(accountsHook, 'useAccountsOverview').mockReturnValue({
      data: null,
      loading: false,
      error: 'Failed to load',
      refetch: vi.fn(),
    })
    vi.spyOn(profilesHook, 'useProfiles').mockReturnValue({
      profiles: [],
      loading: false,
      error: null,
      setActiveProfile: vi.fn(),
      refetch: vi.fn(),
    })

    render(
      <BrowserRouter>
        <AccountsPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/Failed to load/)).toBeInTheDocument()
  })

  it('should render accounts successfully', async () => {
    vi.spyOn(accountsHook, 'useAccountsOverview').mockReturnValue({
      data: mockAccountsData,
      loading: false,
      error: null,
      refetch: vi.fn(),
    })
    vi.spyOn(profilesHook, 'useProfiles').mockReturnValue({
      profiles: mockProfiles,
      loading: false,
      error: null,
      setActiveProfile: vi.fn(),
      refetch: vi.fn(),
    })

    render(
      <BrowserRouter>
        <AccountsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Your accounts')).toBeInTheDocument()
    })

    expect(screen.getByText('Current Account')).toBeInTheDocument()
    expect(screen.getByText('12-34-56 | ****5678')).toBeInTheDocument()
    expect(screen.getByText('£1,248.36')).toBeInTheDocument()
  })

  it('should render unavailable account with error message', async () => {
    const unavailableData = {
      ...mockAccountsData,
      accounts: [
        {
          ...mockAccountsData.accounts[0],
          current_balance_minor: null,
          source_status: 'unavailable',
        },
      ],
    }

    vi.spyOn(accountsHook, 'useAccountsOverview').mockReturnValue({
      data: unavailableData,
      loading: false,
      error: null,
      refetch: vi.fn(),
    })
    vi.spyOn(profilesHook, 'useProfiles').mockReturnValue({
      profiles: mockProfiles,
      loading: false,
      error: null,
      setActiveProfile: vi.fn(),
      refetch: vi.fn(),
    })

    render(
      <BrowserRouter>
        <AccountsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Unavailable')).toBeInTheDocument()
    })

    expect(screen.getByText(/We can't show this balance right now/)).toBeInTheDocument()
  })

  it('should render loans', async () => {
    const dataWithLoan = {
      ...mockAccountsData,
      loans: [
        {
          loan_snapshot_id: 'loan-1',
          profile_id: 'profile-1',
          external_loan_ref: 'loan_7781',
          loan_name: 'Personal Loan',
          outstanding_balance_minor: 486000,
          next_repayment_minor: 21250,
          next_repayment_date: '2024-11-28',
          currency_code: 'GBP',
          freshness_at: '2024-01-01T09:00:00Z',
          source_status: 'available',
        },
      ],
    }

    vi.spyOn(accountsHook, 'useAccountsOverview').mockReturnValue({
      data: dataWithLoan,
      loading: false,
      error: null,
      refetch: vi.fn(),
    })
    vi.spyOn(profilesHook, 'useProfiles').mockReturnValue({
      profiles: mockProfiles,
      loading: false,
      error: null,
      setActiveProfile: vi.fn(),
      refetch: vi.fn(),
    })

    render(
      <BrowserRouter>
        <AccountsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Personal Loan')).toBeInTheDocument()
    })

    expect(screen.getByText('£4,860.00')).toBeInTheDocument()
    expect(screen.getByText(/Next repayment:/)).toBeInTheDocument()
  })

  it('should not render profile switcher when only one profile', async () => {
    vi.spyOn(accountsHook, 'useAccountsOverview').mockReturnValue({
      data: mockAccountsData,
      loading: false,
      error: null,
      refetch: vi.fn(),
    })
    vi.spyOn(profilesHook, 'useProfiles').mockReturnValue({
      profiles: mockProfiles,
      loading: false,
      error: null,
      setActiveProfile: vi.fn(),
      refetch: vi.fn(),
    })

    render(
      <BrowserRouter>
        <AccountsPage />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Your accounts')).toBeInTheDocument()
    })

    expect(screen.queryByRole('tablist')).not.toBeInTheDocument()
  })
})
