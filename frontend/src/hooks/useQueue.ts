import { useState, useCallback } from 'react'
import { apiClient } from '../lib/api-client'
import type { QueueListResponse, QueueRefreshRequest, RefreshRunResponse } from '../types/queue'

export interface QueueFilters {
  queue_state?: string
  non_standard?: boolean
  customer_id?: string
  assigned_to_me?: boolean
  limit?: number
  offset?: number
}

export function useQueue() {
  const [data, setData] = useState<QueueListResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchQueue = useCallback(async (filters: QueueFilters = {}) => {
    setIsLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (filters.queue_state) params.set('queue_state', filters.queue_state)
      if (filters.non_standard !== undefined) params.set('non_standard', String(filters.non_standard))
      if (filters.customer_id) params.set('customer_id', filters.customer_id)
      if (filters.assigned_to_me !== undefined) params.set('assigned_to_me', String(filters.assigned_to_me))
      if (filters.limit) params.set('limit', String(filters.limit))
      if (filters.offset) params.set('offset', String(filters.offset))

      const query = params.toString()
      const response = await apiClient.get<QueueListResponse>(
        `/v1/queue-items${query ? `?${query}` : ''}`
      )
      setData(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load queue')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const triggerRefresh = useCallback(async (request: QueueRefreshRequest): Promise<RefreshRunResponse> => {
    return await apiClient.post<RefreshRunResponse>('/v1/queue-items/refresh', request)
  }, [])

  const checkRefreshStatus = useCallback(async (runId: string): Promise<RefreshRunResponse> => {
    return await apiClient.get<RefreshRunResponse>(`/v1/queue-items/refresh-runs/${runId}`)
  }, [])

  return {
    data,
    isLoading,
    error,
    fetchQueue,
    triggerRefresh,
    checkRefreshStatus,
  }
}
