/**
 * Hook for creating scam claims
 */

import { useState } from 'react'
import { post } from '../../lib/api-client'

export interface CreateScamClaimRequest {
  payment_order_id?: string
  claim_reason_code: string
  notes?: string
}

export interface ScamClaim {
  scam_claim_id: string
  claim_reference: string
  claim_status: string
  claim_reason_code: string
  reported_at: string
  support_case_reference?: string
  fraud_case_reference?: string
  payment_order_id?: string
  created_at: string
  updated_at: string
}

export function useCreateScamClaim() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createScamClaim = async (
    request: CreateScamClaimRequest
  ): Promise<ScamClaim | null> => {
    setLoading(true)
    setError(null)

    try {
      const data = await post<ScamClaim>('/support/scam-claims', request)
      return data
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to create scam claim'
      setError(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }

  return {
    createScamClaim,
    loading,
    error,
  }
}
