import { useState } from 'react'
import { apiClient } from '../lib/api-client'
import { PromiseCreateRequest, PromiseResponse, PolicyFailureDetail } from '../types/promise'

export function usePromises() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [policyFailure, setPolicyFailure] = useState<PolicyFailureDetail | null>(null)

  const createPromise = async (
    request: PromiseCreateRequest,
    idempotencyKey: string
  ): Promise<PromiseResponse | null> => {
    setLoading(true)
    setError(null)
    setPolicyFailure(null)

    try {
      const response = await apiClient.post<PromiseResponse>('/v1/promises', request, {
        headers: {
          'Idempotency-Key': idempotencyKey,
        },
      })
      return response
    } catch (err: unknown) {
      if (err instanceof Error) {
        // Try to parse policy failure details from error
        try {
          const errorData = JSON.parse(err.message)
          if (errorData.detail && typeof errorData.detail === 'object' && errorData.detail.failed_conditions) {
            setPolicyFailure(errorData.detail as PolicyFailureDetail)
          } else {
            setError(err.message)
          }
        } catch {
          setError(err.message)
        }
      } else {
        setError('Failed to create promise')
      }
      return null
    } finally {
      setLoading(false)
    }
  }

  return { createPromise, loading, error, policyFailure }
}
