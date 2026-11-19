/**
 * Hook for approving a payment
 */

import { useState } from 'react'
import { post } from '../../lib/api-client'

export interface ApprovePaymentRequest {
  step_up_challenge_ref?: string
  device_attestation?: string
}

export interface ApprovalResponse {
  payment_order_id: string
  status: string
}

export function useApprovePayment() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const approvePayment = async (
    paymentOrderId: string,
    request: ApprovePaymentRequest
  ): Promise<ApprovalResponse | null> => {
    setLoading(true)
    setError(null)

    try {
      const data = await post<ApprovalResponse>(
        `/payments/${paymentOrderId}/approve`,
        request
      )
      return data
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to approve payment'
      setError(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }

  return {
    approvePayment,
    loading,
    error,
  }
}
