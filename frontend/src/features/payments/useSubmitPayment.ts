/**
 * Hook for submitting a payment
 */

import { useState } from 'react'
import { post } from '../../lib/api-client'

export interface SubmissionResponse {
  payment_order_id: string
  external_payment_ref?: string
  normalized_status: string
  current_internal_state: string
  submitted_at?: string
  expected_arrival_text?: string
}

export function useSubmitPayment() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submitPayment = async (
    paymentOrderId: string
  ): Promise<SubmissionResponse | null> => {
    setLoading(true)
    setError(null)

    try {
      const data = await post<SubmissionResponse>(
        `/payments/${paymentOrderId}/submit`,
        {}
      )
      return data
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to submit payment'
      setError(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }

  return {
    submitPayment,
    loading,
    error,
  }
}
