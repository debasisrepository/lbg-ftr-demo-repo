import { NavLink } from 'react-router-dom';
import { useAuth } from '../../lib/auth-context';

export function Sidebar() {
  const { user } = useAuth();

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `block px-s4 py-s3 rounded-field font-medium transition-colors ${
      isActive
        ? 'bg-primary text-primary-ink'
        : 'text-ink hover:bg-primary-soft'
    }`;

  return (
    <aside className="app-sidebar bg-surface border-r border-line p-s4">
      <nav className="space-y-s2" aria-label="Main navigation">
        <NavLink to="/" className={navLinkClass} end>
          Dashboard
        </NavLink>
        
        {user && !user.is_colleague && (
          <>
            <NavLink to="/resolve" className={navLinkClass}>
              Get help
            </NavLink>
            <NavLink to="/cases" className={navLinkClass}>
              My Cases
            </NavLink>
            <NavLink to="/case-confirmation" className={navLinkClass}>
              Case Confirmation
            </NavLink>
          </>
        )}

        {user?.is_colleague && (
          <NavLink to="/colleague/cases" className={navLinkClass}>
            Team Cases
          </NavLink>
        )}
      </nav>
    </aside>
  );
}
