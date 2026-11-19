/**
 * Application layout with header and navigation
 */

import { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Header,
  HeaderContainer,
  HeaderName,
  HeaderNavigation,
  HeaderMenuItem,
  HeaderGlobalBar,
  HeaderGlobalAction,
  SkipToContent,
  Content,
  Theme,
} from '@carbon/react';
import { Logout } from '@carbon/icons-react';
import { useAuth } from '../../lib/auth-context';

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Theme theme="white">
      <HeaderContainer
        render={() => (
          <>
            <Header aria-label="LBG Demo Platform">
              <SkipToContent />
              <HeaderName href="/" prefix="">
                Your Bank
              </HeaderName>
              <HeaderNavigation aria-label="Main Navigation">
                <HeaderMenuItem href="/accounts">
                  Accounts
                </HeaderMenuItem>
                <HeaderMenuItem href="/dashboard">
                  Dashboard
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
            <Content id="main-content">{children}</Content>
          </>
        )}
      />
    </Theme>
  );
}
