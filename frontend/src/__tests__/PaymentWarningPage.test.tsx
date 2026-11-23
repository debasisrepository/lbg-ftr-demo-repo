import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { PaymentWarningPage } from '../pages/PaymentWarningPage';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({
      state: {
        payment: {
          payment_id: 'pay-123',
          current_state: 'warning_presented',
          customer_visible_status: null,
          payment_reference: 'Invoice 2041',
          amount_minor: 25000,
          currency: 'GBP',
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
          warning: {
            heading: 'This payment may be a scam',
            body: 'We have seen payments like this used by fraudsters. Once you send money you may not get it back.',
            allowed_actions: ['stop', 'continue'],
            policy_allows_continue: true,
          },
        },
      },
    }),
  };
});

describe('PaymentWarningPage', () => {
  it('renders warning heading and body', () => {
    render(
      <BrowserRouter>
        <PaymentWarningPage />
      </BrowserRouter>
    );

    expect(screen.getByRole('heading', { name: 'This payment may be a scam' })).toBeInTheDocument();
    const bodyTexts = screen.getAllByText(/We have seen payments like this used by fraudsters/);
    expect(bodyTexts[0]).toBeInTheDocument();
  });

  it('renders payment details', () => {
    render(
      <BrowserRouter>
        <PaymentWarningPage />
      </BrowserRouter>
    );

    expect(screen.getByText('K Evans Lettings')).toBeInTheDocument();
    expect(screen.getByText('£250.00')).toBeInTheDocument();
    expect(screen.getByText('Invoice 2041')).toBeInTheDocument();
  });

  it('renders stop button', () => {
    render(
      <BrowserRouter>
        <PaymentWarningPage />
      </BrowserRouter>
    );

    expect(screen.getByRole('button', { name: /stop this payment/i })).toBeInTheDocument();
  });

  it('renders continue button when policy allows', () => {
    render(
      <BrowserRouter>
        <PaymentWarningPage />
      </BrowserRouter>
    );

    expect(screen.getByRole('button', { name: /i understand the risk, continue/i })).toBeInTheDocument();
  });

  it('focuses warning heading on mount', async () => {
    render(
      <BrowserRouter>
        <PaymentWarningPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      const heading = screen.getByRole('heading', { name: 'This payment may be a scam' });
      expect(heading).toHaveFocus();
    });
  });

  it('renders warning tips', () => {
    render(
      <BrowserRouter>
        <PaymentWarningPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Be careful if someone asked you to move money quickly/)).toBeInTheDocument();
    expect(screen.getByText(/Your bank will never ask you to move money to a safe account/)).toBeInTheDocument();
    expect(screen.getByText(/If you are not sure, stop and speak to someone you trust/)).toBeInTheDocument();
  });

  it('has alertdialog role', () => {
    render(
      <BrowserRouter>
        <PaymentWarningPage />
      </BrowserRouter>
    );

    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
  });
});
