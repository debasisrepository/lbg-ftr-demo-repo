/**
 * Hook for checking payment status with polling
 */

import { useState, useEffect, useCallback } from 'react'
import { get } from '../../lib/api-client'

export interface PaymentStatus {
  payment_order_id: string
  customer_payment_ref: string
  payment_reference: string
  amount_minor: number
  currency_code: string
  payee_name: string
  normalized_status: string
  current_internal_state: string
  external_payment_ref?: string
  expected_arrival_text?: string
  submitted_at?: string
  created_at: string
  updated_at: string
}

export function usePaymentStatus(paymentOrderId: string | null, pollWhilePending = true) {
  const [status, setStatus] = useState<PaymentStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    if (!paymentOrderId) return

    setLoading(true)
    setError(null)

    try {
      const data = await get<PaymentStatus>(`/payments/${paymentOrderId}`)
      setStatus(data)

      // Stop polling if status is no longer pending
      if (data.normalized_status !== 'pending') {
        return false // Signal to stop polling
      }
      return true // Continue polling
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to fetch payment status'
      setError(errorMessage)
      return false
    } finally {
      setLoading(false)
    }
  }, [paymentOrderId])

  useEffect(() => {
    if (!paymentOrderId || !pollWhilePending) {
      return
    }

    // Initial fetch
    let shouldContinue = true
    fetchStatus().then((continuePolling) => {
      shouldContinue = continuePolling !== false
    })

    // Poll every 5 seconds if status is pending
    const interval = setInterval(async () => {
      if (!shouldContinue) {
        clearInterval(interval)
        return
      }

      const continuePolling = await fetchStatus()
      if (continuePolling === false) {
        shouldContinue = false
        clearInterval(interval)
      }
    }, 5000)

    return () => clearInterval(interval)
  }, [paymentOrderId, pollWhilePending, fetchStatus])

  return {
    status,
    loading,
    error,
    refetch: fetchStatus,
  }
}
