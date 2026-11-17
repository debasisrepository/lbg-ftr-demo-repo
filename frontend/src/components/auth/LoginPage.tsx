import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth-context';
import { ApiError } from '../../lib/api-client';

export function LoginPage() {
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login({ email, password });
      navigate('/');
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail || 'Login failed');
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper">
      <div className="w-full max-w-md">
        <div className="bg-surface border border-line rounded-card p-s6 shadow-lg">
          <h1 className="font-head text-3xl font-bold text-ink mb-s5">
            Sign in to Clear Path
          </h1>

          {error && (
            <div className="mb-s4 p-s3 bg-warn-bg text-warn-ink rounded-field border border-warn-ink">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-s4">
            <div>
              <label htmlFor="email" className="block font-bold mb-s2 text-ink">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-s3 py-s3 border-2 border-muted rounded-field focus:outline-none focus:border-primary"
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label htmlFor="password" className="block font-bold mb-s2 text-ink">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-s3 py-s3 border-2 border-muted rounded-field focus:outline-none focus:border-primary"
                required
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full min-h-[48px] px-s4 py-s3 bg-primary text-primary-ink font-bold rounded-button border-2 border-primary hover:bg-opacity-90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-s4 text-sm text-muted text-center">
            <p>Default credentials: admin@example.com / admin123</p>
          </div>
        </div>
      </div>
    </div>
  );
}
