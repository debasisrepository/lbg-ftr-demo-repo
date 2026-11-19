import { useState, useEffect } from 'react'
import { get, put } from '../../lib/api-client'

export interface ProfileEntitlement {
  entitlement_id: string
  profile_id: string
  entitlement_code: string
  capability_type: string
  can_view_accounts: boolean
  can_manage_payees: boolean
  can_initiate_payments: boolean
  effective_from: string | null
  effective_to: string | null
}

export interface ProfileInfo {
  profile_id: string
  customer_id: string
  profile_type: string
  display_name: string
  status: string
  entitlements: ProfileEntitlement[]
}

export interface ProfileListResponse {
  profiles: ProfileInfo[]
}

export interface SetActiveProfileRequest {
  profile_id: string
}

export interface SetActiveProfileResponse {
  profile_id: string
  display_name: string
  message: string
}

export function useProfiles() {
  const [profiles, setProfiles] = useState<ProfileInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProfiles = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await get<ProfileListResponse>('/profiles')
      setProfiles(response.profiles)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profiles')
    } finally {
      setLoading(false)
    }
  }

  const setActiveProfile = async (profileId: string): Promise<void> => {
    try {
      await put<SetActiveProfileResponse>('/profiles/active', {
        profile_id: profileId,
      })
      // Profiles list doesn't need refresh - active profile is managed server-side
    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Failed to set active profile')
    }
  }

  useEffect(() => {
    fetchProfiles()
  }, [])

  return { profiles, loading, error, setActiveProfile, refetch: fetchProfiles }
}
