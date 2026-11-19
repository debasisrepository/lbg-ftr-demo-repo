/**
 * Hook for preparing a payment
 */

import { useState } from 'react'
import { post } from '../../lib/api-client'

export interface PreparePaymentRequest {
  source_account_id: string
  payee_id: string
  amount_minor: number
  currency_code: string
  payment_reference: string
  idempotency_key: string
}

export interface PreparedPayment {
  payment_order_id: string
  customer_payment_ref: string
  payment_reference: string
  amount_minor: number
  currency_code: string
  source_account_name: string
  payee_name: string
  limit_checks_passed: boolean
  risk_decision: string
  requires_approval: boolean
  dynamic_link_digest: string
}

export interface PaymentLimit {
  message: string
  limit_type: string
  available_amount_minor: number
}

export function usePreparePayment() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const preparePayment = async (
    request: PreparePaymentRequest
  ): Promise<{ data?: PreparedPayment; limitError?: PaymentLimit }> => {
    setLoading(true)
    setError(null)

    try {
      const data = await post<PreparedPayment>('/payments/prepare', request)
      return { data }
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to prepare payment'

      // Check for limit error (contains "up to" or "limit" in message)
      if (
        errorMessage.includes('up to') ||
        errorMessage.includes('limit') ||
        errorMessage.includes('balance')
      ) {
        setError(errorMessage)
        return {
          limitError: {
            message: errorMessage,
            limit_type: 'balance',
            available_amount_minor: 0,
          },
        }
      }

      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    preparePayment,
    loading,
    error,
  }
}
