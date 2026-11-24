import { useAuth } from '../../lib/use-auth'
import { useNavigate } from 'react-router-dom'

export function Header() {
  const { user, activeRole, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <header className="bg-primary text-white shadow-md">
      <div className="max-w-full px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold">Receivables & Collections</h1>
          {activeRole && (
            <span className="text-sm bg-primary-dark px-3 py-1 rounded-full">
              {activeRole.role_label}
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-4">
          {user && (
            <>
              <div className="text-sm">
                <div className="font-medium">{user.display_name}</div>
                <div className="text-primary-light text-xs">{user.email}</div>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-primary-dark hover:bg-primary-light hover:text-primary transition-colors rounded"
              >
                Logout
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
