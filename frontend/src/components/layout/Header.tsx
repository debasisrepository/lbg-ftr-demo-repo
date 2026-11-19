/**
 * Application header component
 * - App branding
 * - User info display
 * - Sign out action
 */

import { useAuth } from '../../lib/auth-context'
import sharedConfig from '../../../../shared_config.json'

export function Header() {
  const { user, logout } = useAuth()

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* App branding */}
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">
              {sharedConfig.app_name}
            </h1>
          </div>

          {/* User info and actions */}
          {user && (
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-700">
                <span className="font-medium">{user.username}</span>
                {user.auth_level && (
                  <span className="ml-2 text-xs text-gray-500">
                    ({user.auth_level})
                  </span>
                )}
              </div>
              <button
                onClick={logout}
                className="text-sm text-gray-600 hover:text-gray-900 focus:outline-none focus:underline"
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
