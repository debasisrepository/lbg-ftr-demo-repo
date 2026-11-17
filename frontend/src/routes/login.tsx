import { useState, FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button, TextInput, Form, Stack } from '@carbon/react';
import { useAuth } from '../lib/auth-context';

/**
 * Login page with email/password form
 * Defaults match seed credentials: admin@example.com / admin123
 */
export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  
  const [username, setUsername] = useState('admin@example.com');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/cases';
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    
    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: 'var(--cds-background)',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '400px',
          padding: 'var(--cds-spacing-05)',
        }}
      >
        <Stack gap={6}>
          <h1 className="cds--productive-heading-04">Sign in to LBG Clear Path</h1>
          
          {error && (
            <div
              style={{
                padding: 'var(--cds-spacing-05)',
                backgroundColor: 'var(--cds-support-error)',
                color: 'var(--cds-text-on-color)',
                borderRadius: '4px',
              }}
            >
              {error}
            </div>
          )}
          
          <Form onSubmit={handleSubmit}>
            <Stack gap={5}>
              <TextInput
                id="username"
                labelText="Email or Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
              />
              
              <TextInput
                id="password"
                type="password"
                labelText="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
              
              <Button
                type="submit"
                disabled={isLoading}
                style={{ width: '100%' }}
              >
                {isLoading ? 'Signing in...' : 'Sign in'}
              </Button>
            </Stack>
          </Form>
        </Stack>
      </div>
    </div>
  );
}
