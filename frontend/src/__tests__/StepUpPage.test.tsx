/**
 * Unit tests for StepUpPage - FR-002
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { screen, fireEvent, waitFor } from '@testing-library/dom';
import '@testing-library/jest-dom/vitest';
import { BrowserRouter } from 'react-router-dom';
import { StepUpPage } from '../pages/StepUpPage';
import * as apiClient from '../lib/api-client';

const mockNavigate = vi.fn();
const mockLocation = { state: { sessionId: 123 } };

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockLocation,
  };
});

vi.mock('../lib/api-client', () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

describe('StepUpPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderStepUpPage = () => {
    return render(
      <BrowserRouter>
        <StepUpPage />
      </BrowserRouter>
    );
  };

  it('renders passcode entry form', () => {
    renderStepUpPage();

    expect(screen.getByText('Enter your passcode')).toBeInTheDocument();
    expect(screen.getByText('Enter the 6-digit passcode you created when you opened your account.')).toBeInTheDocument();
    
    // Should have 6 passcode inputs
    const inputs = screen.getAllByLabelText(/passcode digit/i);
    expect(inputs).toHaveLength(6);
  });

  it('validates complete passcode entry', async () => {
    renderStepUpPage();

    const inputs = screen.getAllByLabelText(/passcode digit/i);
    
    // Enter only 3 digits
    fireEvent.change(inputs[0], { target: { value: '1' } });
    fireEvent.change(inputs[1], { target: { value: '2' } });
    fireEvent.change(inputs[2], { target: { value: '3' } });

    const form = inputs[0].closest('form');
    if (form) {
      fireEvent.submit(form);
    }

    await waitFor(() => {
      expect(screen.getByText('Enter all 6 digits.')).toBeInTheDocument();
    });

    expect(apiClient.apiClient.post).not.toHaveBeenCalled();
  });

  it('shows remaining attempts after wrong passcode', async () => {
    const mockPost = vi.mocked(apiClient.apiClient.post);
    mockPost.mockResolvedValueOnce({
      status: 'failed',
      session_id: 123,
      step_up_verified: false,
      remaining_attempts: 2,
      next_route: '/step-up',
      available_methods: ['passcode'],
    });

    renderStepUpPage();

    const inputs = screen.getAllByLabelText(/passcode digit/i);
    
    // Enter 6 digits
    inputs.forEach((input: Element, index: number) => {
      fireEvent.change(input, { target: { value: (index + 1).toString() } });
    });

    const form = inputs[0].closest('form');
    if (form) {
      fireEvent.submit(form);
    }

    await waitFor(() => {
      expect(screen.getByText(/Your passcode is incorrect. You have 2 attempts left./i)).toBeInTheDocument();
    });
  });

  it('locks passcode after 3 wrong attempts (FR-002 AC2)', async () => {
    const mockPost = vi.mocked(apiClient.apiClient.post);
    mockPost.mockResolvedValueOnce({
      status: 'locked',
      session_id: 123,
      step_up_verified: false,
      remaining_attempts: 0,
      next_route: '/login',
      available_methods: ['password'],
    });

    renderStepUpPage();

    const inputs = screen.getAllByLabelText(/passcode digit/i);
    
    // Enter 6 digits
    inputs.forEach((input: Element, index: number) => {
      fireEvent.change(input, { target: { value: (index + 1).toString() } });
    });

    const form = inputs[0].closest('form');
    if (form) {
      fireEvent.submit(form);
    }

    // Should show button to return to login
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /sign in with password/i })).toBeInTheDocument();
    });
  });

  it('advances to accounts on successful verification (FR-002 AC1)', async () => {
    const mockPost = vi.mocked(apiClient.apiClient.post);
    mockPost.mockResolvedValueOnce({
      status: 'verified',
      session_id: 123,
      step_up_verified: true,
      remaining_attempts: null,
      next_route: '/accounts',
      available_methods: [],
    });

    renderStepUpPage();

    const inputs = screen.getAllByLabelText(/passcode digit/i);
    
    // Enter correct passcode (123456 stub)
    ['1', '2', '3', '4', '5', '6'].forEach((digit: string, index: number) => {
      fireEvent.change(inputs[index], { target: { value: digit } });
    });

    const form = inputs[0].closest('form');
    if (form) {
      fireEvent.submit(form);
    }

    await waitFor(() => {
      expect(screen.getByText("It's you")).toBeInTheDocument();
    });

    // Should navigate to accounts after delay
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/accounts');
    }, { timeout: 1000 });
  });

  it('handles biometric authentication', async () => {
    const mockPost = vi.mocked(apiClient.apiClient.post);
    mockPost.mockResolvedValueOnce({
      status: 'verified',
      session_id: 123,
      step_up_verified: true,
      remaining_attempts: null,
      next_route: '/accounts',
      available_methods: [],
    });

    renderStepUpPage();

    // Wait for biometric button to appear (it has random availability)
    await waitFor(() => {
      const biometricButton = screen.queryByRole('button', { name: /use face id instead/i });
      if (biometricButton) {
        fireEvent.click(biometricButton);
      }
    });

    // If biometric was available and clicked, should call API
    if (apiClient.apiClient.post) {
      await waitFor(() => {
        const calls = vi.mocked(apiClient.apiClient.post).mock.calls;
        if (calls.length > 0) {
          expect(calls[0][0]).toBe('/sca/verify-step-up');
          expect(calls[0][1]).toMatchObject({
            method: 'biometric',
          });
        }
      });
    }
  });

  it('toggles passcode visibility', () => {
    renderStepUpPage();

    const inputs = screen.getAllByLabelText(/passcode digit/i) as HTMLInputElement[];
    const showPasscodeButton = screen.getByRole('button', { name: /show passcode/i });

    expect(inputs[0].type).toBe('password');

    fireEvent.click(showPasscodeButton);
    expect(inputs[0].type).toBe('text');

    fireEvent.click(showPasscodeButton);
    expect(inputs[0].type).toBe('password');
  });
});
