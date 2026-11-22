import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { AccountsPage } from '../pages/AccountsPage'

// Mock hooks
vi.mock('../features/accounts/useAccountsOverview', () => ({
  useAccountsOverview: vi.fn(),
}))

vi.mock('../features/accounts/useProfiles', () => ({
  useProfiles: vi.fn(),
}))

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

import { useAccountsOverview } from '../features/accounts/useAccountsOverview'
import { useProfiles } from '../features/accounts/useProfiles'

describe('AccountsPage - Enhancements', () => {
  const mockAccountsData = {
    accounts: [
      {
        bank_account_id: 'account-1',
        account_name: 'Personal Current',
        account_type: 'current_account',
        currency_code: 'GBP',
        current_balance_minor: 125000,
        available_balance_minor: 125000,
        overdraft_limit_minor: 50000,
        sort_code_masked: '12-34-56',
        account_number_masked: '****7890',
        source_status: 'fresh',
        payment_permission: true,
        freshness_at: new Date().toISOString(),
      },
      {
        bank_account_id: 'account-2',
        account_name: 'Business Account',
        account_type: 'current_account',
        currency_code: 'GBP',
        current_balance_minor: 500000,
        available_balance_minor: 500000,
        overdraft_limit_minor: 100000,
        sort_code_masked: '98-76-54',
        account_number_masked: '****1234',
        source_status: 'fresh',
        payment_permission: false, // No payment permission
        freshness_at: new Date().toISOString(),
      },
    ],
    loans: [
      {
        loan_snapshot_id: 'loan-1',
        profile_id: 'profile-1',
        loan_name: 'Personal Loan',
        outstanding_balance_minor: 500000,
        next_repayment_minor: 25000,
        next_repayment_date: '2024-02-15',
        currency_code: 'GBP',
        external_loan_ref: 'LOAN123456',
        source_status: 'fresh',
        freshness_at: new Date().toISOString(),
      },
      {
        loan_snapshot_id: 'loan-2',
        profile_id: 'profile-1',
        loan_name: 'Mortgage',
        outstanding_balance_minor: 25000000,
        next_repayment_minor: 120000,
        next_repayment_date: '2024-02-01',
        currency_code: 'GBP',
        external_loan_ref: 'MORT789012',
        source_status: 'fresh',
        freshness_at: new Date().toISOString(),
      },
    ],
    profile_id: 'profile-1',
    profile_display_name: 'Sasha Patel',
  }

  const mockProfiles = {
    profiles: [
      {
        profile_id: 'profile-1',
        customer_id: 'customer-1',
        profile_type: 'personal',
        display_name: 'Personal',
        status: 'active',
        entitlements: [],
      },
      {
        profile_id: 'profile-2',
        customer_id: 'customer-1',
        profile_type: 'business',
        display_name: 'Business',
        status: 'active',
        entitlements: [],
      },
    ],
    loading: false,
    error: null,
    setActiveProfile: vi.fn(),
    refetch: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useAccountsOverview).mockReturnValue({
      data: mockAccountsData,
      loading: false,
      error: null,
      refetch: vi.fn(),
    })
    vi.mocked(useProfiles).mockReturnValue(mockProfiles)
  })

  describe('Loan Display (BR-ACCT-004)', () => {
    it('should display loans with outstanding balance', () => {
      render(
        <BrowserRouter>
          <AccountsPage />
        </BrowserRouter>
      )

      expect(screen.getByText('Personal Loan')).toBeInTheDocument()
      expect(screen.getByText('Mortgage')).toBeInTheDocument()

      // Check outstanding balances are displayed
      expect(screen.getByText(/£5,000.00/)).toBeInTheDocument()
      expect(screen.getByText(/£250,000.00/)).toBeInTheDocument()
    })

    it('should display next repayment amount and date', () => {
      render(
        <BrowserRouter>
          <AccountsPage />
        </BrowserRouter>
      )

      // Check next repayment information is visible
      expect(screen.getByText(/Next repayment/)).toBeInTheDocument()
      expect(screen.getByText(/£250.00/)).toBeInTheDocument()
      expect(screen.getByText(/£1,200.00/)).toBeInTheDocument()
      
      // Check dates are formatted correctly
      expect(screen.getByText(/15 Feb/)).toBeInTheDocument()
      expect(screen.getByText(/1 Feb/)).toBeInTheDocument()
    })

    it('should display loan reference number', () => {
      render(
        <BrowserRouter>
          <AccountsPage />
        </BrowserRouter>
      )

      // Check last 4 digits of loan ref are shown
      expect(screen.getByText(/Loan ending 3456/)).toBeInTheDocument()
      expect(screen.getByText(/Loan ending 9012/)).toBeInTheDocument()
    })

    it('should handle loan with missing repayment data gracefully', () => {
      const dataWithIncompleteLoans = {
        ...mockAccountsData,
        loans: [
          {
            ...mockAccountsData.loans[0],
            next_repayment_minor: null,
            next_repayment_date: null,
          },
        ],
      }

      vi.mocked(useAccountsOverview).mockReturnValue({
        data: dataWithIncompleteLoans,
        loading: false,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <BrowserRouter>
          <AccountsPage />
        </BrowserRouter>
      )

      // Should still display loan name and balance
      expect(screen.getByText('Personal Loan')).toBeInTheDocument()
      expect(screen.getByText(/£5,000.00/)).toBeInTheDocument()
      
      // Should not crash due to missing repayment data
    })
  })

  describe('Profile Switching (BR-ACCT-002)', () => {
    it('should display profile switcher when multiple profiles exist', () => {
      render(
        <BrowserRouter>
          <AccountsPage />
        </BrowserRouter>
      )

      expect(screen.getByRole('tab', { name: 'Personal' })).toBeInTheDocument()
      expect(screen.getByRole('tab', { name: 'Business' })).toBeInTheDocument()
    })

    it('should call setActiveProfile when switching profiles', async () => {
      const user = userEvent.setup()
      const mockSetActiveProfile = vi.fn().mockResolvedValue(undefined)
      const mockRefetch = vi.fn()

      vi.mocked(useProfiles).mockReturnValue({
        ...mockProfiles,
        setActiveProfile: mockSetActiveProfile,
      })

      vi.mocked(useAccountsOverview).mockReturnValue({
        data: mockAccountsData,
        loading: false,
        error: null,
        refetch: mockRefetch,
      })

      render(
        <BrowserRouter>
          <AccountsPage />
        </BrowserRouter>
      )

      const businessTab = screen.getByRole('tab', { name: 'Business' })
      await user.click(businessTab)

      await waitFor(() => {
        expect(mockSetActiveProfile).toHaveBeenCalledWith('profile-2')
      })
    })

    it('should refresh accounts after profile switch', async () => {
      const user = userEvent.setup()
      const mockSetActiveProfile = vi.fn().mockResolvedValue(undefined)
      const mockRefetch = vi.fn()

      vi.mocked(useProfiles).mockReturnValue({
        ...mockProfiles,
        setActiveProfile: mockSetActiveProfile,
      })

      vi.mocked(useAccountsOverview).mockReturnValue({
        data: mockAccountsData,
        loading: false,
        error: null,
        refetch: mockRefetch,
      })

      render(
        <BrowserRouter>
          <AccountsPage />
        </BrowserRouter>
      )

      const businessTab = screen.getByRole('tab', { name: 'Business' })
      await user.click(businessTab)

      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled()
      })
    })
  })

  describe('Payment Permissions (BR-ACCT-003)', () => {
    it('should display accounts regardless of payment permission', () => {
      render(
        <BrowserRouter>
          <AccountsPage />
        </BrowserRouter>
      )

      // Both accounts should be visible
      expect(screen.getByText('Personal Current')).toBeInTheDocument()
      expect(screen.getByText('Business Account')).toBeInTheDocument()
    })

    it('should show different balances for accounts with different permissions', () => {
      render(
        <BrowserRouter>
          <AccountsPage />
        </BrowserRouter>
      )

      // Check both balances are displayed
      expect(screen.getByText(/£1,250.00/)).toBeInTheDocument()
      expect(screen.getByText(/£5,000.00/)).toBeInTheDocument()
    })

    // Note: The actual enforcement of payment permission would be tested
    // in integration tests or E2E tests where the payment flow is triggered
  })

  describe('Data Freshness (CMP-CON-02)', () => {
    it('should handle unavailable data gracefully', () => {
      const dataWithUnavailable = {
        ...mockAccountsData,
        accounts: [
          {
            ...mockAccountsData.accounts[0],
            source_status: 'unavailable',
            current_balance_minor: null,
          },
        ],
      }

      vi.mocked(useAccountsOverview).mockReturnValue({
        data: dataWithUnavailable,
        loading: false,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <BrowserRouter>
          <AccountsPage />
        </BrowserRouter>
      )

      expect(screen.getByText('Unavailable')).toBeInTheDocument()
      expect(screen.getByText(/can't show this balance right now/i)).toBeInTheDocument()
    })

    it('should display staleness indicator for stale data', () => {
      const staleTime = new Date()
      staleTime.setHours(staleTime.getHours() - 1)

      const dataWithStale = {
        ...mockAccountsData,
        accounts: [
          {
            ...mockAccountsData.accounts[0],
            source_status: 'stale',
            freshness_at: staleTime.toISOString(),
          },
        ],
      }

      vi.mocked(useAccountsOverview).mockReturnValue({
        data: dataWithStale,
        loading: false,
        error: null,
        refetch: vi.fn(),
      })

      render(
        <BrowserRouter>
          <AccountsPage />
        </BrowserRouter>
      )

      expect(screen.getByText(/Balance as at/)).toBeInTheDocument()
    })
  })
})
