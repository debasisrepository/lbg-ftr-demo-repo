import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../lib/auth-context';

export function Header() {
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();

  return (
    <header className="bg-primary text-white shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <h1 className="text-2xl font-bold">LBG FTR Demo</h1>
            
            {isAuthenticated && (
              <nav className="flex space-x-4" aria-label="Main navigation">
                <Link
                  to="/accounts"
                  className={`px-3 py-2 rounded transition-colors ${
                    location.pathname === '/accounts'
                      ? 'bg-white text-primary font-medium'
                      : 'hover:bg-primary-dark'
                  }`}
                >
                  Accounts
                </Link>
                <Link
                  to="/payees"
                  className={`px-3 py-2 rounded transition-colors ${
                    location.pathname.startsWith('/payees') || location.pathname.startsWith('/payment')
                      ? 'bg-white text-primary font-medium'
                      : 'hover:bg-primary-dark'
                  }`}
                >
                  Pay &amp; Transfer
                </Link>
                <Link
                  to="/payment-sent"
                  className={`px-3 py-2 rounded transition-colors ${
                    location.pathname.startsWith('/payment-sent')
                      ? 'bg-white text-primary font-medium'
                      : 'hover:bg-primary-dark'
                  }`}
                >
                  Payment Sent
                </Link>
                <Link
                  to="/payment-failed"
                  className={`px-3 py-2 rounded transition-colors ${
                    location.pathname.startsWith('/payment-failed')
                      ? 'bg-white text-primary font-medium'
                      : 'hover:bg-primary-dark'
                  }`}
                >
                  Payment Failed
                </Link>
              </nav>
            )}
          </div>
          
          {isAuthenticated && user && (
            <div className="flex items-center space-x-4">
              <span className="text-sm">
                Welcome, <span className="font-semibold">{user.display_name}</span>
              </span>
              <button
                onClick={logout}
                className="px-4 py-2 bg-white text-primary rounded hover:bg-gray-100 transition-colors text-sm font-medium"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
