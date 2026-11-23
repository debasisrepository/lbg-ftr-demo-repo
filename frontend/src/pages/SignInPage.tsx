import { useState, useEffect, FormEvent } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../lib/auth-context';

export function SignInPage() {
  const [passcode, setPasscode] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const { login, isLoading, error, isAuthenticated, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Clear errors when component mounts or when user starts typing
  useEffect(() => {
    clearError();
    setLocalError(null);
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/accounts';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!passcode || passcode.length < 4 || passcode.length > 12) {
      setLocalError('Passcode must be between 4 and 12 characters.');
      return;
    }

    try {
      await login({
        device_identifier: 'device-CUST-SYNTH-001-iOS',
        mobile_platform: 'iOS',
        passcode,
      });
    } catch (err) {
      // Error is handled by auth context
    }
  };

  const displayError = error || localError;
  const sessionEndedMessage = location.state && (location.state as { sessionEnded?: boolean }).sessionEnded;

  return (
    <div className="min-h-screen flex flex-col bg-gray-100">
      {/* Status bar */}
      <div className="h-11 flex items-center px-6 text-sm font-bold bg-[#002563] text-white">
        <span>9:41</span>
      </div>

      {/* Brand header */}
      <div className="flex items-center gap-3 px-4 py-3 bg-[#002563] text-white">
        <div className="w-8 h-8 rounded-lg bg-[#0074CD] flex items-center justify-center text-sm font-bold">
          YB
        </div>
        <span className="font-bold text-lg">Your Bank</span>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col gap-4 p-6">
        <h1 className="text-[28px] leading-tight font-bold text-[#002563] mb-0">Sign in</h1>
        <p className="text-base text-[#575756] leading-relaxed mb-2">
          Enter your passcode to see your accounts. You can sign in on this registered device only.
        </p>

        {/* Session ended reconnect message */}
        {sessionEndedMessage && (
          <div className="flex gap-3 p-4 rounded-lg border-l-4 border-[#0074CD] bg-[#F2FAFF]" role="status">
            <svg className="w-5 h-5 flex-shrink-0 text-[#0074CD]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 11v6M12 7.5v.5" />
            </svg>
            <div>
              <strong className="block text-[#002563] font-bold">Your session ended</strong>
              <span className="text-[#002563]">Sign in to continue. We will show you where your payment is.</span>
            </div>
          </div>
        )}

        {/* Error message */}
        {displayError && (
          <div className="flex gap-3 p-4 rounded-lg border-2 border-[#BE222A] bg-white" role="alert">
            <svg className="w-5 h-5 flex-shrink-0 text-[#BE222A]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3l10 18H2z" />
              <path d="M12 10v5M12 18v.5" />
            </svg>
            <div>
              <strong className="block font-bold">Sign-in failed</strong>
              <span>{displayError}</span>
            </div>
          </div>
        )}

        {/* Sign-in form */}
        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          <div>
            <label htmlFor="passcode" className="block mb-1 text-sm font-bold text-black">
              Passcode
            </label>
            <input
              id="passcode"
              name="passcode"
              type="password"
              autoComplete="current-password"
              aria-describedby="passcode-hint"
              minLength={4}
              maxLength={12}
              required
              value={passcode}
              onChange={(e) => {
                setPasscode(e.target.value);
                setLocalError(null);
                clearError();
              }}
              aria-invalid={!!displayError}
              className={`block w-full h-14 px-4 text-base text-black bg-white border rounded-lg ${
                displayError ? 'border-2 border-[#BE222A]' : 'border border-[#767676]'
              }`}
            />
            {displayError && (
              <p className="flex gap-2 mt-1 text-sm font-bold text-[#BE222A]" id="passcode-error">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 3l10 18H2z" />
                  <path d="M12 10v5M12 18v.5" />
                </svg>
                <span>Enter your passcode again.</span>
              </p>
            )}
            {!displayError && (
              <p className="mt-1 text-sm text-[#4F5155]" id="passcode-hint">
                4 to 12 characters. We never show or store it.
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="flex items-center justify-center gap-2 w-full min-h-[48px] px-6 font-bold text-white bg-[#0074CD] border-2 border-[#0074CD] rounded-lg disabled:bg-[#E0E0E0] disabled:border-[#E0E0E0] disabled:text-[#4F5155]"
          >
            {isLoading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        {/* Protected content notice */}
        <div className="flex gap-3 p-4 rounded-lg border-l-4 border-[#0074CD] bg-[#F2FAFF] text-[#002563]">
          <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
            <rect x="5" y="11" width="14" height="10" rx="2" />
            <path d="M8 11V8a4 4 0 018 0v3" />
          </svg>
          <span>Protected content appears only after you sign in.</span>
        </div>
      </div>
    </div>
  );
}
