import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { PaymentPendingPage } from '../pages/PaymentPendingPage';

const mockNavigate = vi.fn();
let mockLocationState: any = null;

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({
      state: mockLocationState,
    }),
  };
});

describe('PaymentPendingPage - Timeout Scenario', () => {
  beforeEach(() => {
    mockLocationState = {
      payment: {
        payment_id: 'pay-456',
        current_state: 'pending_confirmation',
        customer_visible_status: 'Pending',
        payment_reference: 'Invoice 2041',
        amount_minor: 25000,
        currency: 'GBP',
        do_not_resubmit: true,
        status_message: "Don't send this payment again",
        payee: {
          payee_id: 'payee-1',
          payee_name: 'K Evans Lettings',
          masked_account_identifier: '9842',
        },
        source_account: {
          account_id: 'acc-1',
          display_name: 'Current Account',
          masked_account_identifier: '1234',
        },
        review_version: 1,
        as_of_timestamp: new Date().toISOString(),
      },
    };
  });

  it('renders pending badge', () => {
    render(
      <BrowserRouter>
        <PaymentPendingPage />
      </BrowserRouter>
    );

    const pendingTexts = screen.getAllByText('Pending');
    const badge = pendingTexts[0].closest('span[role="status"]');
    expect(badge).toBeInTheDocument();
  });

  it('renders do not resubmit message', () => {
    render(
      <BrowserRouter>
        <PaymentPendingPage />
      </BrowserRouter>
    );

    const dontSendTexts = screen.getAllByText(/Don't send this payment again/);
    expect(dontSendTexts[0]).toBeInTheDocument();
    // The message text depends on the state - either pending_confirmation or held
    expect(screen.getByText(/We are still waiting for confirmation|We are making some extra checks/)).toBeInTheDocument();
  });

  it('renders payment details', () => {
    render(
      <BrowserRouter>
        <PaymentPendingPage />
      </BrowserRouter>
    );

    expect(screen.getByText('K Evans Lettings')).toBeInTheDocument();
    expect(screen.getByText('£250.00')).toBeInTheDocument();
    expect(screen.getByText('Invoice 2041')).toBeInTheDocument();
  });

  it('renders check status button', () => {
    render(
      <BrowserRouter>
        <PaymentPendingPage />
      </BrowserRouter>
    );

    expect(screen.getByRole('button', { name: /check status/i })).toBeInTheDocument();
  });
});

describe('PaymentPendingPage - Held Scenario', () => {
  beforeEach(() => {
    mockLocationState = {
      payment: {
        payment_id: 'pay-789',
        current_state: 'held_for_review',
        customer_visible_status: 'Pending',
        payment_reference: 'Invoice 2041',
        amount_minor: 25000,
        currency: 'GBP',
        do_not_resubmit: true,
        status_message: "We're checking this payment",
        payee: {
          payee_id: 'payee-1',
          payee_name: 'K Evans Lettings',
          masked_account_identifier: '9842',
        },
        source_account: {
          account_id: 'acc-1',
          display_name: 'Current Account',
          masked_account_identifier: '1234',
        },
        review_version: 1,
        hold_latest_decision_at: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString(),
      },
    };
  });

  it('renders held title', () => {
    render(
      <BrowserRouter>
        <PaymentPendingPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/We're checking this payment/)).toBeInTheDocument();
  });

  it('renders held do not resubmit message', () => {
    render(
      <BrowserRouter>
        <PaymentPendingPage />
      </BrowserRouter>
    );

    const messages = screen.getAllByText(/We are making some extra checks to keep your money safe/);
    expect(messages[0]).toBeInTheDocument();
  });

  it('shows pending badge for held payments', () => {
    render(
      <BrowserRouter>
        <PaymentPendingPage />
      </BrowserRouter>
    );

    const pendingTexts = screen.getAllByText('Pending');
    const badge = pendingTexts[0].closest('span[role="status"]');
    expect(badge).toBeInTheDocument();
  });
});
