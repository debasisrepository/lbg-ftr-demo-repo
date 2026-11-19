import { useState, useEffect } from 'react'
import { get } from '../../lib/api-client'

export interface CopCheckOut {
  cop_check_id: string
  outcome: string
  suggested_name: string | null
  policy_treatment: string
  checked_at: string
  expires_at: string | null
  customer_acknowledged_at: string | null
}

export interface PayeeOut {
  payee_id: string
  customer_id: string
  profile_id: string | null
  payee_name: string
  sort_code: string
  account_number_masked: string
  payee_type: string
  is_saved: boolean
  status: string
  last_verified_at: string | null
  latest_cop_check: CopCheckOut | null
}

export interface PayeeListResponse {
  payees: PayeeOut[]
}

export function usePayees() {
  const [payees, setPayees] = useState<PayeeOut[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPayees = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await get<PayeeListResponse>('/payees')
      setPayees(response.payees)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load payees')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPayees()
  }, [])

  return { payees, loading, error, refetch: fetchPayees }
}
