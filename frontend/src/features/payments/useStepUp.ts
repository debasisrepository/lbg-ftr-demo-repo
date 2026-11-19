/**
 * Hook for creating step-up challenges
 */

import { useState } from 'react'
import { post } from '../../lib/api-client'

export interface StepUpChallenge {
  challenge_ref: string
  expires_at: string
}

export function useStepUp() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createStepUp = async (context: {
    action: string
    resource_type: string
    resource_id: string
  }): Promise<StepUpChallenge | null> => {
    setLoading(true)
    setError(null)

    try {
      const data = await post<StepUpChallenge>('/auth/step-up', context)
      return data
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to create step-up challenge'
      setError(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }

  return {
    createStepUp,
    loading,
    error,
  }
}
