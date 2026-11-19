/**
 * Unit tests for LoginPage - FR-001
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { screen, fireEvent, waitFor } from '@testing-library/dom';
import '@testing-library/jest-dom/vitest';
import { BrowserRouter } from 'react-router-dom';
import { LoginPage } from '../pages/LoginPage';
import * as apiClient from '../lib/api-client';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../lib/api-client', () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  const renderLoginPage = () => {
    return render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );
  };

  it('renders login form with seed credentials pre-filled', () => {
    renderLoginPage();

    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.getByText('Use the username and password you set up when you opened your account.')).toBeInTheDocument();
    
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    
    expect(usernameInput).toHaveValue('admin@example.com');
    expect(passwordInput).toHaveValue('admin123');
  });

  it('shows inline validation when fields are empty (FR-001 AC1)', async () => {
    renderLoginPage();

    // Clear the pre-filled values
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    
    fireEvent.change(usernameInput, { target: { value: '' } });
    fireEvent.change(passwordInput, { target: { value: '' } });

    const submitButton = screen.getByRole('button', { name: /continue/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Enter your username.')).toBeInTheDocument();
      expect(screen.getByText('Enter your password.')).toBeInTheDocument();
    });

    // Should not call API when fields are empty
    expect(apiClient.apiClient.post).not.toHaveBeenCalled();
  });

  it('shows generic error for incorrect credentials (FR-001 AC2)', async () => {
    const mockPost = vi.mocked(apiClient.apiClient.post);
    mockPost.mockRejectedValueOnce(new Error('Unauthorized'));

    renderLoginPage();

    const submitButton = screen.getByRole('button', { name: /continue/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Sign-in failed')).toBeInTheDocument();
      expect(screen.getByText("We couldn't sign you in with those details.")).toBeInTheDocument();
    });
  });

  it('shows rate limit warning on too many attempts', async () => {
    const mockPost = vi.mocked(apiClient.apiClient.post);
    mockPost.mockRejectedValueOnce(new Error('Too many sign-in attempts. Try again shortly.'));

    renderLoginPage();

    const submitButton = screen.getByRole('button', { name: /continue/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Please wait')).toBeInTheDocument();
      expect(screen.getByText('Too many sign-in attempts. Try again shortly.')).toBeInTheDocument();
    });
  });

  it('advances to step-up on successful login (FR-001 AC3)', async () => {
    const mockPost = vi.mocked(apiClient.apiClient.post);
    mockPost.mockResolvedValueOnce({
      access_token: 'test-token',
      token_type: 'Bearer',
      expires_in_seconds: 28800,
      session_id: 123,
      step_up_required: true,
      available_step_up_methods: ['passcode', 'biometric'],
    });

    renderLoginPage();

    const submitButton = screen.getByRole('button', { name: /continue/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Details accepted')).toBeInTheDocument();
    });

    // Token should be stored
    expect(localStorage.getItem('lbg_ftr_auth_token')).toBe('test-token');

    // Should navigate to step-up after delay
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/step-up', { state: { sessionId: 123 } });
    }, { timeout: 1000 });
  });

  it('toggles password visibility', () => {
    renderLoginPage();

    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement;
    const showPasswordButton = screen.getByRole('button', { name: /show password/i });

    expect(passwordInput.type).toBe('password');

    fireEvent.click(showPasswordButton);
    expect(passwordInput.type).toBe('text');

    fireEvent.click(showPasswordButton);
    expect(passwordInput.type).toBe('password');
  });
});
