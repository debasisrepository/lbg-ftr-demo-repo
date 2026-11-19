import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import PaymentEntryPage from '../pages/PaymentEntryPage';
import * as apiClient from '../lib/api-client';

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock navigation
const mockNavigate = vi.fn();
const mockUseLocation = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockUseLocation(),
  };
});

// Mock API client
vi.mock('../lib/api-client');

describe('PaymentEntryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Set up default location state
    mockUseLocation.mockReturnValue({
      state: {
        payee: {
          payee_id: 1,
          display_name: 'Jamie Clarke',
          sort_code: '04-00-04',
          masked_account_number: '****3746',
          can_proceed: true,
        },
        account: {
          account_id: 2,
          account_name: 'Current Account',
          sort_code: '00-03-20',
          masked_account_number: '****5920',
          available_balance_minor: 124836,
          current_balance_minor: 124836,
          currency: 'GBP',
          account_type: 'current_account',
          freshness_state: 'current',
          last_updated_at: '2026-11-19T10:00:00Z',
        },
      },
    });
  });

  it('renders payment entry form with payee and account details', () => {
    render(
      <BrowserRouter>
        <PaymentEntryPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Make a payment')).toBeInTheDocument();
    expect(screen.getByText('Jamie Clarke')).toBeInTheDocument();
    expect(screen.getByText('04-00-04 · ****3746')).toBeInTheDocument();
    expect(screen.getByLabelText('From')).toHaveValue('Current Account · 00-03-20 | ****5920');
    // Use a function matcher to handle text split across elements or formatted numbers
    expect(screen.getByText((content, element) => {
      return element?.textContent === 'Available balance £1,248.36';
    })).toBeInTheDocument();
  });

  it('shows amount exceeds balance error when amount is too high', async () => {
    const user = userEvent.setup();
    
    vi.mocked(apiClient.post).mockResolvedValue({
      payment_id: 1,
      amount_minor: 150000,
      currency: 'GBP',
      payee: {
        payee_id: 1,
        display_name: 'Jamie Clarke',
        sort_code: '04-00-04',
        masked_account_number: '****3746',
      },
      balance_check: {
        passed: false,
        available_balance_minor: 124836,
        detail: 'Payment amount exceeds available balance. You can pay up to £1,248.36 from this account.',
      },
      limit_check: { passed: true, configured_limit_minor: 1000000 },
      fraud_decision: { decision: 'allow' },
    });

    render(
      <BrowserRouter>
        <PaymentEntryPage />
      </BrowserRouter>
    );

    const amountInput = screen.getByLabelText('Amount');
    await user.clear(amountInput);
    await user.type(amountInput, '1500.00');

    // Find the Pay button - it will say "Pay £1500.00" with the amount entered
    const payButton = screen.getByRole('button', { name: (name) => name.startsWith('Pay £') && name.includes('1500') });
    await user.click(payButton);

    await waitFor(() => {
      expect(screen.getByText(/Payment amount exceeds available balance/i)).toBeInTheDocument();
    });
  });

  it('shows fraud warning modal when fraud decision is warn', async () => {
    const user = userEvent.setup();
    
    vi.mocked(apiClient.post).mockResolvedValue({
      payment_id: 1,
      amount_minor: 25000,
      currency: 'GBP',
      payee: {
        payee_id: 1,
        display_name: 'Jamie Clarke',
        sort_code: '04-00-04',
        masked_account_number: '****3746',
      },
      balance_check: { passed: true, available_balance_minor: 124836 },
      limit_check: { passed: true, configured_limit_minor: 1000000 },
      fraud_decision: {
        decision: 'warn',
        warning_message: 'Check this payment carefully. Fraudsters can pretend to be landlords or suppliers.',
      },
      approval_required: true,
      approval_challenge: {
        challenge_id: 42,
        challenge_expires_at: '2026-11-19T12:00:00Z',
        dynamic_link_summary: {
          payee_name: 'Jamie Clarke',
          amount_minor: 25000,
          currency: 'GBP',
        },
      },
    });

    render(
      <BrowserRouter>
        <PaymentEntryPage />
      </BrowserRouter>
    );

    const payButton = screen.getByRole('button', { name: /Pay £250.00/i });
    await user.click(payButton);

    // Wait for warning modal to appear by checking for the modal heading
    await waitFor(() => {
      expect(screen.getByText('Check this payment carefully')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('shows approval modal after successful preparation', async () => {
    const user = userEvent.setup();
    
    vi.mocked(apiClient.post).mockResolvedValue({
      payment_id: 1,
      amount_minor: 25000,
      currency: 'GBP',
      payee: {
        payee_id: 1,
        display_name: 'Jamie Clarke',
        sort_code: '04-00-04',
        masked_account_number: '****3746',
      },
      balance_check: { passed: true, available_balance_minor: 124836 },
      limit_check: { passed: true, configured_limit_minor: 1000000 },
      fraud_decision: { decision: 'allow' },
      approval_required: true,
      approval_challenge: {
        challenge_id: 42,
        challenge_expires_at: '2026-11-19T12:00:00Z',
        dynamic_link_summary: {
          payee_name: 'Jamie Clarke',
          amount_minor: 25000,
          currency: 'GBP',
        },
      },
    });

    render(
      <BrowserRouter>
        <PaymentEntryPage />
      </BrowserRouter>
    );

    const payButton = screen.getByRole('button', { name: /Pay £250.00/i });
    await user.click(payButton);

    // Wait for the modal content to appear
    await waitFor(() => {
      // Modal heading appears - it's rendered even before the modal role
      expect(screen.getByText('Approve with Face ID')).toBeInTheDocument();
    });
    
    // Verify the modal summary shows payee and amount (there are now 2 "Jamie Clarke" on the page - one in payee panel, one in modal)
    const jamieClarkElements = screen.getAllByText('Jamie Clarke');
    expect(jamieClarkElements.length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('£250.00')).toBeInTheDocument();
  });

  it('navigates to outcome page after successful approval', async () => {
    const user = userEvent.setup();
    
    const mockPrepareResponse = {
      payment_id: 1,
      amount_minor: 25000,
      currency: 'GBP',
      payee: {
        payee_id: 1,
        display_name: 'Jamie Clarke',
        sort_code: '04-00-04',
        masked_account_number: '****3746',
      },
      balance_check: { passed: true, available_balance_minor: 124836 },
      limit_check: { passed: true, configured_limit_minor: 1000000 },
      fraud_decision: { decision: 'allow' },
      approval_required: true,
      approval_challenge: {
        challenge_id: 42,
        challenge_expires_at: '2026-11-19T12:00:00Z',
        dynamic_link_summary: {
          payee_name: 'Jamie Clarke',
          amount_minor: 25000,
          currency: 'GBP',
        },
      },
    };

    const mockApproveResponse = {
      payment_id: 1,
      status: 'sent',
      amount_minor: 25000,
      currency: 'GBP',
      payee: {
        payee_id: 1,
        display_name: 'Jamie Clarke',
      },
      reference: 'Invoice 2041',
      payment_reference: 'PAY-20261119-000417',
      expected_arrival_message: 'Funds will arrive by end of business today.',
      duplicate_submission_blocked: false,
      next_actions: [],
    };

    // Setup mock to return different responses for each call
    const postMock = vi.mocked(apiClient.post);
    postMock
      .mockResolvedValueOnce(mockPrepareResponse)
      .mockResolvedValueOnce(mockApproveResponse);

    render(
      <BrowserRouter>
        <PaymentEntryPage />
      </BrowserRouter>
    );

    const payButton = screen.getByRole('button', { name: /Pay £250.00/i });
    await user.click(payButton);

    // Wait for the modal to open
    await waitFor(() => {
      expect(screen.getByText('Approve with Face ID')).toBeInTheDocument();
    });

    // Find and click the Approve button - wait for it to be interactive
    const approveButton = await screen.findByRole('button', { name: 'Approve' });
    expect(approveButton).toBeInTheDocument();
    await user.click(approveButton);

    // Wait for navigation to be called
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/payment/outcome', {
        state: { payment: mockApproveResponse },
      });
    }, { timeout: 3000 });
  });

  it('enforces reference character limit of 18', async () => {
    const user = userEvent.setup();

    render(
      <BrowserRouter>
        <PaymentEntryPage />
      </BrowserRouter>
    );

    const referenceInput = screen.getByLabelText('Reference (optional)');
    await user.type(referenceInput, '123456789012345678901234567890');

    expect(referenceInput).toHaveValue('123456789012345678');
  });
});
