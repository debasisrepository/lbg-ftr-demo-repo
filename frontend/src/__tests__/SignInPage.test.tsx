import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { SignInPage } from '../pages/SignInPage';
import { AuthProvider } from '../lib/auth-context';
import * as apiClient from '../lib/api-client';

// Mock the api-client module
vi.mock('../lib/api-client', () => ({
  apiClient: {
    post: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(message: string, public status: number, public detail?: string) {
      super(message);
      this.name = 'ApiError';
    }
  },
}));

const renderSignInPage = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <SignInPage />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('SignInPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
  });

  it('renders sign-in form with passcode input', () => {
    renderSignInPage();
    
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/passcode/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('shows hint text for passcode field', () => {
    renderSignInPage();
    
    expect(screen.getByText(/4 to 12 characters/i)).toBeInTheDocument();
  });

  it('shows protected content notice', () => {
    renderSignInPage();
    
    expect(screen.getByText(/protected content appears only after you sign in/i)).toBeInTheDocument();
  });

  it('validates passcode length before submission', async () => {
    renderSignInPage();
    
    const passcodeInput = screen.getByLabelText(/passcode/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    // Enter too short passcode
    fireEvent.change(passcodeInput, { target: { value: 'ab' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/enter your passcode again/i)).toBeInTheDocument();
    });
    
    expect(apiClient.apiClient.post).not.toHaveBeenCalled();
  });

  it('calls login API with correct credentials on form submission', async () => {
    const mockResponse = {
      access_token: 'test-token',
      token_type: 'Bearer',
      expires_in: 3600,
      expires_at: '2026-11-22T12:00:00Z',
      inactivity_timeout_seconds: 900,
      session_id: 'test-session-id',
      user: {
        id: 'test-user-id',
        display_name: 'Test User',
        profile_type: 'personal',
      },
    };
    
    vi.mocked(apiClient.apiClient.post).mockResolvedValueOnce(mockResponse);
    
    renderSignInPage();
    
    const passcodeInput = screen.getByLabelText(/passcode/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    fireEvent.change(passcodeInput, { target: { value: 'Pass1234' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(apiClient.apiClient.post).toHaveBeenCalledWith('/v1/auth/login', {
        device_identifier: 'device-CUST-SYNTH-001-iOS',
        mobile_platform: 'iOS',
        passcode: 'Pass1234',
      });
    });
  });

  it('shows error message on login failure', async () => {
    const mockError = new (apiClient as any).ApiError('Login failed', 401, 'Invalid credentials');
    vi.mocked(apiClient.apiClient.post).mockRejectedValueOnce(mockError);
    
    renderSignInPage();
    
    const passcodeInput = screen.getByLabelText(/passcode/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    fireEvent.change(passcodeInput, { target: { value: 'WrongPass' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/sign-in failed/i)).toBeInTheDocument();
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });

  it('disables submit button during loading', async () => {
    vi.mocked(apiClient.apiClient.post).mockImplementation(() => new Promise(() => {}));
    
    renderSignInPage();
    
    const passcodeInput = screen.getByLabelText(/passcode/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    fireEvent.change(passcodeInput, { target: { value: 'Pass1234' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
      expect(screen.getByText(/signing in/i)).toBeInTheDocument();
    });
  });

  it('clears error when user starts typing', async () => {
    const mockError = new (apiClient as any).ApiError('Login failed', 401, 'Invalid credentials');
    vi.mocked(apiClient.apiClient.post).mockRejectedValueOnce(mockError);
    
    renderSignInPage();
    
    const passcodeInput = screen.getByLabelText(/passcode/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    // Trigger error
    fireEvent.change(passcodeInput, { target: { value: 'WrongPass' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
    
    // Start typing again
    fireEvent.change(passcodeInput, { target: { value: 'NewPass' } });
    
    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });
});
