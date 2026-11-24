import { useState, useEffect } from 'react'
import { apiClient } from '../lib/api-client'
import { Customer360Response } from '../types/customer'

export function useCustomerView(customerId: string | undefined) {
  const [data, setData] = useState<Customer360Response | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!customerId) return

    const fetchCustomerView = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await apiClient.get<Customer360Response>(
          `/v1/customers/${customerId}/view`
        )
        setData(response)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load customer view')
      } finally {
        setLoading(false)
      }
    }

    fetchCustomerView()
  }, [customerId])

  return { data, loading, error }
}
