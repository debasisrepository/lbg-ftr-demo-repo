/**
 * Login page - FR-001 Sign in
 * Wireframe: wireframe_01_j01_s01.html
 */

import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, TextInput, InlineNotification, Link, Theme } from '@carbon/react';
import { ChevronRight, View } from '@carbon/icons-react';
import { apiClient } from '../lib/api-client';
import './LoginPage.module.scss';

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  session_id: number;
  step_up_required: boolean;
  available_step_up_methods: string[];
  active_profile_id?: number;
}

export function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState('admin@example.com');
  const [password, setPassword] = useState('admin123');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // Validation and error states
  const [usernameError, setUsernameError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [genericError, setGenericError] = useState('');
  const [rateLimitWarning, setRateLimitWarning] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    // Clear all errors
    setUsernameError('');
    setPasswordError('');
    setGenericError('');
    setRateLimitWarning('');
    setSuccessMessage('');

    // Inline validation for empty fields (FR-001 AC1)
    let hasError = false;
    if (!username.trim()) {
      setUsernameError('Enter your username.');
      hasError = true;
    }
    if (!password.trim()) {
      setPasswordError('Enter your password.');
      hasError = true;
    }

    if (hasError) {
      return; // Do not submit
    }

    setLoading(true);

    try {
      const response = await apiClient.post<LoginResponse>('/auth/login', {
        username,
        password,
      });

      // Store token
      localStorage.setItem('lbg_ftr_auth_token', response.access_token);
      
      // Show success and advance to step-up
      setSuccessMessage('Details accepted');
      
      // Navigate to step-up after brief delay
      setTimeout(() => {
        navigate('/step-up', { state: { sessionId: response.session_id } });
      }, 500);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Request failed';
      
      // Handle rate limiting (429 response)
      if (errorMessage.includes('Too many')) {
        setRateLimitWarning(errorMessage);
      } else {
        // Generic error message (FR-001 AC2) - does not reveal which credential was wrong
        setGenericError("We couldn't sign you in with those details.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Theme theme="white">
      <div className="login-container">
      <header className="login-topbar">
        <button 
          className="login-back-btn" 
          type="button" 
          aria-label="Back"
          onClick={() => navigate(-1)}
        >
          <svg className="login-icon login-icon-16" width="16" height="16" aria-hidden="true">
            <polygon points="6.7,12.3 2.9,8.5 15,8.5 15,7.5 2.9,7.5 6.7,3.7 6,3 1,8 6,13"/>
          </svg>
        </button>
        <span className="login-brand">Your Bank</span>
      </header>

      <main className="login-content">
        <h1 className="login-heading">Login</h1>
        <p className="login-lead">Use the username and password you set up when you opened your account.</p>

        {/* Success notification (State D) */}
        {successMessage && (
          <InlineNotification
            kind="success"
            title="Details accepted"
            subtitle="Next: prove it's you with your passcode or Face ID."
            lowContrast
            hideCloseButton
            role="status"
            aria-live="polite"
          />
        )}

        {/* Generic error notification (State B) - FR-001 AC2 */}
        {genericError && (
          <InlineNotification
            kind="error"
            title="Sign-in failed"
            subtitle={genericError}
            lowContrast
            hideCloseButton
            role="alert"
            aria-live="assertive"
          />
        )}

        {/* Rate limit warning (State C) */}
        {rateLimitWarning && (
          <InlineNotification
            kind="warning"
            title="Please wait"
            subtitle="Too many sign-in attempts. Try again shortly."
            lowContrast
            hideCloseButton
            role="alert"
            aria-live="assertive"
          />
        )}

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <div className="login-field">
            <TextInput
              id="username"
              name="username"
              type="text"
              labelText="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              invalid={!!usernameError}
              invalidText={usernameError}
              autoComplete="username"
            />
          </div>

          <div className="login-field">
            <TextInput
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              labelText="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              invalid={!!passwordError}
              invalidText={passwordError}
              autoComplete="current-password"
            />
            <div className="login-field-actions">
              <Link href="#recover">Forgotten your details?</Link>
              <button
                className="login-link"
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-pressed={showPassword}
              >
                <View size={16} aria-hidden="true" />
                <span>Show password</span>
              </button>
            </div>
          </div>

          <Button
            type="submit"
            kind="primary"
            className="login-btn-primary"
            disabled={loading || !!rateLimitWarning}
            renderIcon={ChevronRight}
          >
            Continue
          </Button>
        </form>

        <p className="login-helper">
          First time on this device, locked out of your passcode, or chose "Not me"? 
          Sign in here, then we'll check it's you.
        </p>
      </main>
    </div>
    </Theme>
  );
}
