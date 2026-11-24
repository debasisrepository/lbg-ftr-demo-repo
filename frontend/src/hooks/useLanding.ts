import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '../lib/api-client'
import type { LandingResponse, ActiveRoleRequest, ActiveRoleResponse } from '../types/workspace'

export function useLanding() {
  const [data, setData] = useState<LandingResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchLanding = useCallback(async (roleCode?: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const query = roleCode ? `?role_code=${encodeURIComponent(roleCode)}` : ''
      const response = await apiClient.get<LandingResponse>(`/v1/workspace/landing${query}`)
      setData(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load landing data')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const switchRole = useCallback(async (roleCode: string): Promise<ActiveRoleResponse> => {
    const payload: ActiveRoleRequest = { role_code: roleCode }
    const response = await apiClient.put<ActiveRoleResponse>('/v1/workspace/active-role', payload)
    // Refetch landing after role switch
    await fetchLanding()
    return response
  }, [fetchLanding])

  useEffect(() => {
    fetchLanding()
  }, [fetchLanding])

  return {
    data,
    isLoading,
    error,
    refetch: fetchLanding,
    switchRole,
  }
}
