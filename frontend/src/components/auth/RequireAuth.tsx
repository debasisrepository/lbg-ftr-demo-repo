/**
 * Route guard component for proven auth level
 * Redirects to login if not authenticated
 */

import { Navigate } from 'react-router-dom'
import { useAuth } from '../../lib/auth-context'

interface RequireAuthProps {
  children: React.ReactNode
  requiredLevel?: string
}

export function RequireAuth({ children, requiredLevel = 'proven' }: RequireAuthProps) {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // Check auth level if required
  if (requiredLevel && user) {
    const authLevels = ['basic', 'proven', 'elevated']
    const userLevelIndex = authLevels.indexOf(user.auth_level || 'basic')
    const requiredLevelIndex = authLevels.indexOf(requiredLevel)

    if (userLevelIndex < requiredLevelIndex) {
      // Need to step up authentication
      return <Navigate to="/step-up" replace />
    }
  }

  return <>{children}</>
}
