/**
 * Hook for responding to risk warnings/challenges
 */

import { useState } from 'react'
import { post } from '../../lib/api-client'

export interface RiskResponseRequest {
  response_type: 'acknowledged' | 'cancelled' | 'purpose_provided'
  payment_purpose?: string
}

export interface RiskResponseResult {
  payment_order_id: string
  risk_decision: string
  can_proceed: boolean
}

export function useRiskResponse() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const respondToRisk = async (
    paymentOrderId: string,
    request: RiskResponseRequest
  ): Promise<RiskResponseResult | null> => {
    setLoading(true)
    setError(null)

    try {
      const data = await post<RiskResponseResult>(
        `/payments/${paymentOrderId}/risk-response`,
        request
      )
      return data
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to respond to risk check'
      setError(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }

  return {
    respondToRisk,
    loading,
    error,
  }
}
