/**
 * Hook for creating incident reports (BR-OPS-008)
 */

import { useState } from 'react'
import { post } from '../../lib/api-client'

export interface CreateIncidentReportRequest {
  incident_category: string
  incident_title: string
  incident_description?: string
  severity?: string
}

export interface IncidentReport {
  incident_report_id: string
  incident_reference: string
  incident_category: string
  incident_title: string
  incident_description?: string
  severity: string
  status: string
  external_incident_ref?: string
  reported_at: string
  created_at: string
  updated_at: string
}

export function useCreateIncidentReport() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createIncidentReport = async (
    request: CreateIncidentReportRequest
  ): Promise<IncidentReport | null> => {
    setLoading(true)
    setError(null)

    try {
      const data = await post<IncidentReport>('/incidents', request)
      return data
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to create incident report'
      setError(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }

  return {
    createIncidentReport,
    loading,
    error,
  }
}
