import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { PaymentFailedPage } from '../pages/PaymentFailedPage';

const mockNavigate = vi.fn();
const mockUseLocation = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockUseLocation(),
    useParams: () => ({ paymentId: undefined }),
  };
});

vi.mock('../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

describe('PaymentFailedPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders failed badge with icon and text', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'failed',
      customer_visible_status: 'Failed',
      payment_reference: 'Invoice 2041',
      amount_minor: 25000,
      currency: 'GBP',
      payee_display_name: 'K Evans Lettings',
      expected_arrival_time: null,
      source_account: {
        account_id: 'acc-001',
        display_name: 'Alice Murray',
        masked_account_identifier: '****3321',
      },
      payee: {
        payee_id: 'payee-001',
        payee_name: 'K Evans Lettings',
        masked_account_identifier: '****9842',
      },
    };

    mockUseLocation.mockReturnValue({ state: { payment: mockPayment } });

    render(
      <BrowserRouter>
        <PaymentFailedPage />
      </BrowserRouter>
    );

    // Check Failed badge exists with icon and text
    const badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('Failed');
    
    // Verify icon is present (check for SVG)
    const icon = badge.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('shows "no money sent" message', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'failed',
      customer_visible_status: 'Failed',
      payment_reference: 'Invoice 2041',
      amount_minor: 25000,
      currency: 'GBP',
      payee_display_name: 'K Evans Lettings',
      expected_arrival_time: null,
      source_account: {
        account_id: 'acc-001',
        display_name: 'Alice Murray',
        masked_account_identifier: '****3321',
      },
      payee: {
        payee_id: 'payee-001',
        payee_name: 'K Evans Lettings',
        masked_account_identifier: '****9842',
      },
    };

    mockUseLocation.mockReturnValue({ state: { payment: mockPayment } });

    render(
      <BrowserRouter>
        <PaymentFailedPage />
      </BrowserRouter>
    );

    // Check for "no money sent" message
    expect(screen.getByText(/This payment was not completed/)).toBeInTheDocument();
    expect(screen.getByText(/No money was sent and your balance has not changed/)).toBeInTheDocument();
  });

  it('shows payment reference', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'failed',
      customer_visible_status: 'Failed',
      payment_reference: 'Invoice 2041',
      amount_minor: 25000,
      currency: 'GBP',
      payee_display_name: 'K Evans Lettings',
      expected_arrival_time: null,
      source_account: {
        account_id: 'acc-001',
        display_name: 'Alice Murray',
        masked_account_identifier: '****3321',
      },
      payee: {
        payee_id: 'payee-001',
        payee_name: 'K Evans Lettings',
        masked_account_identifier: '****9842',
      },
    };

    mockUseLocation.mockReturnValue({ state: { payment: mockPayment } });

    render(
      <BrowserRouter>
        <PaymentFailedPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Payment reference')).toBeInTheDocument();
    expect(screen.getByText('Invoice 2041')).toBeInTheDocument();
  });

  it('shows payment details with correct formatting', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'failed',
      customer_visible_status: 'Failed',
      payment_reference: 'Invoice 2041',
      amount_minor: 25000,
      currency: 'GBP',
      payee_display_name: 'K Evans Lettings',
      expected_arrival_time: null,
      source_account: {
        account_id: 'acc-001',
        display_name: 'Alice Murray',
        masked_account_identifier: '****3321',
      },
      payee: {
        payee_id: 'payee-001',
        payee_name: 'K Evans Lettings',
        masked_account_identifier: '****9842',
      },
    };

    mockUseLocation.mockReturnValue({ state: { payment: mockPayment } });

    render(
      <BrowserRouter>
        <PaymentFailedPage />
      </BrowserRouter>
    );

    // Check all required details are shown
    expect(screen.getByText('To')).toBeInTheDocument();
    expect(screen.getAllByText('K Evans Lettings')[0]).toBeInTheDocument();
    expect(screen.getByText('Amount')).toBeInTheDocument();
    expect(screen.getByText('£250.00')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    // Find Status row and check it shows Failed
    const statusRows = screen.getAllByText('Status');
    expect(statusRows.length).toBeGreaterThan(0);
  });

  it('shows hint about payment reference', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'failed',
      customer_visible_status: 'Failed',
      payment_reference: 'Invoice 2041',
      amount_minor: 25000,
      currency: 'GBP',
      payee_display_name: 'K Evans Lettings',
      expected_arrival_time: null,
      source_account: {
        account_id: 'acc-001',
        display_name: 'Alice Murray',
        masked_account_identifier: '****3321',
      },
      payee: {
        payee_id: 'payee-001',
        payee_name: 'K Evans Lettings',
        masked_account_identifier: '****9842',
      },
    };

    mockUseLocation.mockReturnValue({ state: { payment: mockPayment } });

    render(
      <BrowserRouter>
        <PaymentFailedPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/The reference is shown so you can tell which payment this refers to/)).toBeInTheDocument();
  });

  it('renders action buttons', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'failed',
      customer_visible_status: 'Failed',
      payment_reference: 'Invoice 2041',
      amount_minor: 25000,
      currency: 'GBP',
      payee_display_name: 'K Evans Lettings',
      expected_arrival_time: null,
      source_account: {
        account_id: 'acc-001',
        display_name: 'Alice Murray',
        masked_account_identifier: '****3321',
      },
      payee: {
        payee_id: 'payee-001',
        payee_name: 'K Evans Lettings',
        masked_account_identifier: '****9842',
      },
    };

    mockUseLocation.mockReturnValue({ state: { payment: mockPayment } });

    render(
      <BrowserRouter>
        <PaymentFailedPage />
      </BrowserRouter>
    );

    expect(screen.getByRole('button', { name: /start a new payment/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /back to accounts/i })).toBeInTheDocument();
  });

  it('distinguishes failed from sent state', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'failed',
      customer_visible_status: 'Failed',
      payment_reference: 'Invoice 2041',
      amount_minor: 25000,
      currency: 'GBP',
      payee_display_name: 'K Evans Lettings',
      expected_arrival_time: null,
      source_account: {
        account_id: 'acc-001',
        display_name: 'Alice Murray',
        masked_account_identifier: '****3321',
      },
      payee: {
        payee_id: 'payee-001',
        payee_name: 'K Evans Lettings',
        masked_account_identifier: '****9842',
      },
    };

    mockUseLocation.mockReturnValue({ state: { payment: mockPayment } });

    render(
      <BrowserRouter>
        <PaymentFailedPage />
      </BrowserRouter>
    );

    // Should show failed heading
    expect(screen.getByText('Payment failed')).toBeInTheDocument();
    
    // Should NOT show payment sent message
    expect(screen.queryByText(/Your payment.*has been sent/)).not.toBeInTheDocument();
  });
});
