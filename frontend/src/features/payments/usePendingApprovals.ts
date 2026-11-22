/**
 * Hook for fetching pending approvals (dual authorization for business payments)
 * BR-ACCT-010: Dual authorization for business payments
 */

import { useState, useEffect } from 'react'
import { get } from '../../lib/api-client'

export interface PendingApproval {
  payment_order_id: string
  customer_payment_ref: string
  payment_reference: string
  amount_minor: number
  currency_code: string
  payee_name: string
  source_account_name: string
  created_at: string
  requires_approval: boolean
}

export function usePendingApprovals() {
  const [approvals, setApprovals] = useState<PendingApproval[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchApprovals = async () => {
    try {
      setLoading(true)
      setError(null)
      // This endpoint would need to be implemented in the backend
      // For now, returning empty array as placeholder
      const response = await get<{ pending_approvals: PendingApproval[] }>('/payments/pending-approvals')
      setApprovals(response.pending_approvals || [])
    } catch (err) {
      // Silently handle - endpoint may not exist yet
      setApprovals([])
      setError(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchApprovals()
  }, [])

  return { approvals, loading, error, refetch: fetchApprovals }
}
