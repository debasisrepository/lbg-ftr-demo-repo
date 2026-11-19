import { useState, useEffect } from 'react'
import { get } from '../../lib/api-client'

export interface AccountOverview {
  bank_account_id: string
  external_account_ref: string | null
  account_type: string
  account_name: string
  sort_code_masked: string | null
  account_number_masked: string | null
  currency_code: string
  account_holder_name: string | null
  current_balance_minor: number | null
  available_balance_minor: number | null
  overdraft_limit_minor: number | null
  freshness_at: string | null
  source_status: string
  payment_permission: boolean
}

export interface LoanOverview {
  loan_snapshot_id: string
  profile_id: string
  external_loan_ref: string | null
  loan_name: string
  outstanding_balance_minor: number | null
  next_repayment_minor: number | null
  next_repayment_date: string | null
  currency_code: string
  freshness_at: string | null
  source_status: string
}

export interface AccountsOverviewResponse {
  accounts: AccountOverview[]
  loans: LoanOverview[]
  profile_id: string
  profile_display_name: string
}

export function useAccountsOverview() {
  const [data, setData] = useState<AccountsOverviewResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAccounts = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await get<AccountsOverviewResponse>('/accounts/overview')
      setData(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load accounts')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAccounts()
  }, [])

  return { data, loading, error, refetch: fetchAccounts }
}
