import { ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Header,
  HeaderName,
  HeaderNavigation,
  HeaderMenuItem,
  HeaderGlobalBar,
  HeaderGlobalAction,
  SkipToContent,
  Theme,
  Content,
} from '@carbon/react';
import { Logout } from '@carbon/icons-react';
import { useAuth } from '../../lib/auth-context';
import styles from './AppLayout.module.css';

interface AppLayoutProps {
  children: ReactNode;
}

/**
 * Application layout with Carbon header and navigation
 */
export function AppLayout({ children }: AppLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, user } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <Theme theme="white">
      <Header aria-label="LBG Clear Path">
        <SkipToContent href="#main-content" />
        <HeaderName href="#" prefix="">
          LBG Clear Path
        </HeaderName>
        <HeaderNavigation aria-label="Main navigation">
          <HeaderMenuItem 
            onClick={() => navigate('/cases')}
            isActive={location.pathname === '/cases' || location.pathname.startsWith('/cases/')}
          >
            My Cases
          </HeaderMenuItem>
          <HeaderMenuItem 
            onClick={() => navigate('/status')}
            isActive={location.pathname === '/status'}
          >
            Service status
          </HeaderMenuItem>
        </HeaderNavigation>
        <HeaderGlobalBar>
          {user && (
            <HeaderGlobalAction
              aria-label="Logout"
              tooltipAlignment="end"
              onClick={handleLogout}
            >
              <Logout size={20} />
            </HeaderGlobalAction>
          )}
        </HeaderGlobalBar>
      </Header>
      <Content id="main-content" className={styles.mainContent}>
        {children}
      </Content>
    </Theme>
  );
}
