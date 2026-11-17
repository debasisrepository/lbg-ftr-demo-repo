import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../lib/auth-context';

interface RequireAuthProps {
  children: React.ReactNode;
}

/**
 * Route guard component - redirects to /login if not authenticated
 */
export function RequireAuth({ children }: RequireAuthProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  
  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100vh' 
      }}>
        <p>Loading...</p>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    // Redirect to login, saving the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return <>{children}</>;
}
