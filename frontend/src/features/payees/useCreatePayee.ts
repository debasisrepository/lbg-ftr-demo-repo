import { useState } from 'react'
import { post } from '../../lib/api-client'
import { CopCheckOut, PayeeOut } from './usePayees'

export interface CreatePayeeRequest {
  payee_name: string
  sort_code: string
  account_number: string
  payee_type: string
}

export interface CreatePayeeResponse {
  payee: PayeeOut
  cop_check: CopCheckOut
}

export function useCreatePayee() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createPayee = async (request: CreatePayeeRequest): Promise<CreatePayeeResponse> => {
    try {
      setLoading(true)
      setError(null)
      const response = await post<CreatePayeeResponse>('/payees', request)
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create payee'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return { createPayee, loading, error }
}
