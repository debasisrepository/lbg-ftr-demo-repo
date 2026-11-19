import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import PaymentOutcomePage from '../pages/PaymentOutcomePage';

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

describe('PaymentOutcomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders sent payment outcome with success details', () => {
    mockUseLocation.mockReturnValue({
      state: {
        payment: {
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
        },
      },
      search: '',
    });

    render(
      <BrowserRouter>
        <PaymentOutcomePage />
      </BrowserRouter>
    );

    expect(screen.getByText('Payment sent')).toBeInTheDocument();
    expect(screen.getByText('Sent')).toBeInTheDocument();
    expect(screen.getByText(/£250.00 is on its way to Jamie Clarke/i)).toBeInTheDocument();
    expect(screen.getByText('Invoice 2041')).toBeInTheDocument();
    expect(screen.getByText('PAY-20261119-000417')).toBeInTheDocument();
  });

  it('renders pending payment outcome with duplicate warning', () => {
    mockUseLocation.mockReturnValue({
      state: {
        payment: {
          payment_id: 2,
          status: 'pending',
          amount_minor: 10000,
          currency: 'GBP',
          payee: {
            payee_id: 1,
            display_name: 'Jamie Clarke',
          },
          payment_reference: 'PAY-PENDING-001',
          duplicate_submission_blocked: true,
        },
      },
      search: '',
    });

    render(
      <BrowserRouter>
        <PaymentOutcomePage />
      </BrowserRouter>
    );

    expect(screen.getByText('Payment pending')).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
    expect(screen.getByText(/We're waiting for confirmation/i)).toBeInTheDocument();
    expect(screen.getByText(/Don't pay again yet/i)).toBeInTheDocument();
    expect(screen.getByText(/Paying again could send the money twice/i)).toBeInTheDocument();
  });

  it('renders failed payment outcome with failure guidance', () => {
    mockUseLocation.mockReturnValue({
      state: {
        payment: {
          payment_id: 3,
          status: 'failed',
          amount_minor: 50000,
          currency: 'GBP',
          payee: {
            payee_id: 2,
            display_name: 'Priya Patel',
          },
          payment_reference: 'PAY-FAILED-001',
          failure_reason: 'Payment could not be completed due to insufficient funds.',
          duplicate_submission_blocked: false,
        },
      },
      search: '',
    });

    render(
      <BrowserRouter>
        <PaymentOutcomePage />
      </BrowserRouter>
    );

    expect(screen.getByText('Payment not sent')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument();
    expect(screen.getByText(/We couldn't send £500.00 to Priya Patel/i)).toBeInTheDocument();
    expect(screen.getByText(/No money has left your account/i)).toBeInTheDocument();
    expect(screen.getByText(/What to do next/i)).toBeInTheDocument();
    expect(screen.getByText(/Payment could not be completed due to insufficient funds/i)).toBeInTheDocument();
  });

  it('shows action buttons appropriate to payment status', () => {
    mockUseLocation.mockReturnValue({
      state: {
        payment: {
          payment_id: 1,
          status: 'sent',
          amount_minor: 25000,
          currency: 'GBP',
          payee: { payee_id: 1, display_name: 'Jamie Clarke' },
          payment_reference: 'PAY-20261119-000417',
          duplicate_submission_blocked: false,
        },
      },
      search: '',
    });

    render(
      <BrowserRouter>
        <PaymentOutcomePage />
      </BrowserRouter>
    );

    expect(screen.getByRole('button', { name: /Back to accounts/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Make another payment/i })).toBeInTheDocument();
  });

  it('disables "Make another payment" button when status is pending', () => {
    mockUseLocation.mockReturnValue({
      state: {
        payment: {
          payment_id: 2,
          status: 'pending',
          amount_minor: 10000,
          currency: 'GBP',
          payee: { payee_id: 1, display_name: 'Jamie Clarke' },
          payment_reference: 'PAY-PENDING-001',
          duplicate_submission_blocked: true,
        },
      },
      search: '',
    });

    render(
      <BrowserRouter>
        <PaymentOutcomePage />
      </BrowserRouter>
    );

    const makeAnotherButton = screen.getByRole('button', { name: /Make another payment/i });
    expect(makeAnotherButton).toBeDisabled();
  });

  it('shows "Try again" button for failed payments', () => {
    mockUseLocation.mockReturnValue({
      state: {
        payment: {
          payment_id: 3,
          status: 'failed',
          amount_minor: 50000,
          currency: 'GBP',
          payee: { payee_id: 2, display_name: 'Priya Patel' },
          payment_reference: 'PAY-FAILED-001',
          duplicate_submission_blocked: false,
        },
      },
      search: '',
    });

    render(
      <BrowserRouter>
        <PaymentOutcomePage />
      </BrowserRouter>
    );

    expect(screen.getByRole('button', { name: /Try again/i })).toBeInTheDocument();
  });

  it('navigates to accounts when back button clicked', async () => {
    const user = userEvent.setup();
    
    mockUseLocation.mockReturnValue({
      state: {
        payment: {
          payment_id: 1,
          status: 'sent',
          amount_minor: 25000,
          currency: 'GBP',
          payee: { payee_id: 1, display_name: 'Jamie Clarke' },
          payment_reference: 'PAY-20261119-000417',
          duplicate_submission_blocked: false,
        },
      },
      search: '',
    });

    render(
      <BrowserRouter>
        <PaymentOutcomePage />
      </BrowserRouter>
    );

    const backButton = screen.getByRole('button', { name: /Back to accounts/i });
    await user.click(backButton);

    expect(mockNavigate).toHaveBeenCalledWith('/accounts');
  });
});
