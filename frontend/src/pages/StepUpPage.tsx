/**
 * Step-up authentication page - FR-002 Prove it's her
 * Wireframe: wireframe_02_j01_s02.html
 */

import { useState, useEffect, useRef, FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button, InlineNotification, Link, Theme } from '@carbon/react';
import { ChevronRight, View, FaceSatisfied } from '@carbon/icons-react';
import { apiClient } from '../lib/api-client';
import './StepUpPage.module.scss';

interface StepUpResponse {
  status: 'verified' | 'failed' | 'locked';
  session_id: number;
  step_up_verified: boolean;
  remaining_attempts: number | null;
  next_route: string;
  available_methods: string[];
}

export function StepUpPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const sessionId = (location.state as { sessionId?: number })?.sessionId;
  
  const [passcode, setPasscode] = useState(['', '', '', '', '', '']);
  const [showPasscode, setShowPasscode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(true);
  
  // Error and status states
  const [passcodeError, setPasscodeError] = useState('');
  const [remainingAttempts, setRemainingAttempts] = useState<number | null>(null);
  const [isLocked, setIsLocked] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [biometricUnavailableInfo, setBiometricUnavailableInfo] = useState('');

  // Refs for input focus management
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    // Redirect to login if no session ID
    if (!sessionId) {
      navigate('/login');
    }

    // Check if biometric is available (stub check)
    // In real app, this would check device capabilities
    const checkBiometric = async () => {
      // For demo: randomly set availability
      const available = Math.random() > 0.3;
      setBiometricAvailable(available);
      if (!available) {
        setBiometricUnavailableInfo("Face ID isn't available on this device");
      }
    };
    checkBiometric();
  }, [sessionId, navigate]);

  const handlePasscodeChange = (index: number, value: string) => {
    // Only allow single digit
    if (value.length > 1) {
      value = value.slice(-1);
    }

    const newPasscode = [...passcode];
    newPasscode[index] = value;
    setPasscode(newPasscode);

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Clear errors when typing
    setPasscodeError('');
  };

  const handlePasscodeKeyDown = (index: number, e: React.KeyboardEvent) => {
    // Handle backspace to move to previous input
    if (e.key === 'Backspace' && !passcode[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
    // Handle Enter to submit the form
    if (e.key === 'Enter') {
      e.preventDefault();
      const form = (e.target as HTMLInputElement).form;
      if (form) {
        form.requestSubmit();
      }
    }
  };

  const handlePasscodeSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    const passcodeValue = passcode.join('');
    
    if (passcodeValue.length < 6) {
      setPasscodeError('Enter all 6 digits.');
      return;
    }

    setLoading(true);
    setPasscodeError('');
    setSuccessMessage('');

    try {
      const response = await apiClient.post<StepUpResponse>('/sca/verify-step-up', {
        session_id: sessionId,
        method: 'passcode',
        passcode: passcodeValue,
        device_id: 'device-001',
      });

      if (response.status === 'verified') {
        // Success - advance to accounts
        setSuccessMessage("It's you");
        setTimeout(() => {
          navigate('/accounts');
        }, 500);
      } else if (response.status === 'locked') {
        // Locked after 3 attempts - redirect to login
        setIsLocked(true);
        setPasscodeError('You entered the wrong passcode 3 times. Sign in with your password to continue.');
      } else if (response.status === 'failed') {
        // Failed attempt - show remaining attempts
        const attempts = response.remaining_attempts || 0;
        setRemainingAttempts(attempts);
        setPasscodeError(`Your passcode is incorrect. You have ${attempts} attempt${attempts === 1 ? '' : 's'} left.`);
        setPasscode(['', '', '', '', '', '']);
        inputRefs.current[0]?.focus();
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Verification failed';
      setPasscodeError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleBiometricAuth = async () => {
    setLoading(true);
    setPasscodeError('');
    setSuccessMessage('');

    try {
      // In real app, this would trigger device biometric prompt
      // For demo, we simulate success
      const response = await apiClient.post<StepUpResponse>('/sca/verify-step-up', {
        session_id: sessionId,
        method: 'biometric',
        biometric_assertion: 'stub-assertion',
        device_id: 'device-001',
      });

      if (response.status === 'verified') {
        setSuccessMessage("It's you");
        setTimeout(() => {
          navigate('/accounts');
        }, 500);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Biometric verification failed';
      setPasscodeError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleReturnToLogin = () => {
    navigate('/login');
  };

  return (
    <Theme theme="white">
      <div className="stepup-container">
      <header className="stepup-topbar">
        <button 
          className="stepup-back-btn" 
          type="button" 
          aria-label="Back"
          onClick={() => navigate(-1)}
        >
          <svg className="stepup-icon stepup-icon-16" width="16" height="16" aria-hidden="true">
            <polygon points="6.7,12.3 2.9,8.5 15,8.5 15,7.5 2.9,7.5 6.7,3.7 6,3 1,8 6,13"/>
          </svg>
        </button>
        <span className="stepup-brand">Your Bank</span>
      </header>

      <main className="stepup-content">
        <h1 className="stepup-heading">Enter your passcode</h1>
        <p className="stepup-lead">Enter the 6-digit passcode you created when you opened your account.</p>

        {/* Success notification (State D) */}
        {successMessage && (
          <InlineNotification
            kind="success"
            title={successMessage}
            subtitle="Taking you to your accounts."
            lowContrast
            hideCloseButton
            role="status"
            aria-live="polite"
          />
        )}

        {/* Biometric unavailable info (State C) - FR-002 AC3 */}
        {biometricUnavailableInfo && !isLocked && (
          <InlineNotification
            kind="info"
            title={biometricUnavailableInfo}
            subtitle="Use your 6-digit passcode instead."
            lowContrast
            hideCloseButton
            role="status"
            aria-live="polite"
          />
        )}

        {/* Locked notification (State B) - FR-002 AC2 */}
        {isLocked && (
          <InlineNotification
            kind="error"
            title="Passcode sign-in paused"
            subtitle="You entered the wrong passcode 3 times. Sign in with your password to continue."
            lowContrast
            hideCloseButton
            role="alert"
            aria-live="assertive"
          />
        )}

        <form className="stepup-form" onSubmit={handlePasscodeSubmit} noValidate>
          <fieldset className={`stepup-passcode-grid ${isLocked ? 'stepup-passcode-locked' : ''}`} disabled={isLocked}>
            <legend className="stepup-legend">Passcode, 6 digits</legend>
            {passcode.map((digit, index) => (
              <input
                key={index}
                ref={(el) => (inputRefs.current[index] = el)}
                className={`stepup-passcode-input ${passcodeError ? 'stepup-passcode-invalid' : ''}`}
                type={showPasscode ? 'text' : 'password'}
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handlePasscodeChange(index, e.target.value)}
                onKeyDown={(e) => handlePasscodeKeyDown(index, e)}
                aria-label={`Passcode digit ${index + 1}`}
                aria-invalid={!!passcodeError}
                autoComplete={index === 0 ? 'one-time-code' : undefined}
                disabled={isLocked}
              />
            ))}
          </fieldset>

          {passcodeError && (
            <p className="stepup-error" role="alert" aria-live="assertive">
              <svg className="stepup-icon stepup-icon-16" width="16" height="16" aria-hidden="true">
                <path d="M8,1C4.1,1,1,4.1,1,8s3.1,7,7,7s7-3.1,7-7S11.9,1,8,1z M10.7,11.5L4.5,5.3l0.8-0.8l6.2,6.2L10.7,11.5z"/>
              </svg>
              <span>{passcodeError}</span>
            </p>
          )}

          <div className="stepup-field-actions">
            <Link href="#recover">Forgotten your passcode?</Link>
            <button
              className="stepup-link"
              type="button"
              onClick={() => setShowPasscode(!showPasscode)}
              aria-pressed={showPasscode}
            >
              <View size={16} aria-hidden="true" />
              <span>Show passcode</span>
            </button>
          </div>
        </form>

        {/* Return to login button when locked (State B) */}
        {isLocked && (
          <Button
            type="button"
            kind="primary"
            className="stepup-btn-primary"
            onClick={handleReturnToLogin}
            renderIcon={ChevronRight}
          >
            Sign in with password
          </Button>
        )}

        {/* Biometric button (State A) - FR-002 AC1 */}
        {biometricAvailable && !isLocked && (
          <button 
            className="stepup-biometric-btn" 
            type="button"
            onClick={handleBiometricAuth}
            disabled={loading}
          >
            <FaceSatisfied size={32} aria-hidden="true" />
            <span>Use Face ID instead</span>
          </button>
        )}

        <p className="stepup-helper">
          After three wrong passcodes, passcode sign-in pauses and you sign in again with your password.
        </p>
      </main>
    </div>
    </Theme>
  );
}
