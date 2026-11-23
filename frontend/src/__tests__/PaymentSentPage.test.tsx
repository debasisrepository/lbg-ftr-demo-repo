import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { PaymentSentPage } from '../pages/PaymentSentPage';

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

describe('PaymentSentPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders sent badge with icon and text', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'completed',
      customer_visible_status: 'Sent',
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
        <PaymentSentPage />
      </BrowserRouter>
    );

    // Check Sent badge exists with icon and text
    const badge = screen.getByRole('status');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('Sent');
    
    // Verify icon is present (check for SVG)
    const icon = badge.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('shows payment reference always', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'completed',
      customer_visible_status: 'Sent',
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
        <PaymentSentPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Payment reference')).toBeInTheDocument();
    expect(screen.getByText('Invoice 2041')).toBeInTheDocument();
  });

  it('shows expected arrival time only when supplied', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'completed',
      customer_visible_status: 'Sent',
      payment_reference: 'Invoice 2041',
      amount_minor: 25000,
      currency: 'GBP',
      payee_display_name: 'K Evans Lettings',
      expected_arrival_time: '2026-11-23T11:41:00Z',
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
        <PaymentSentPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Expected to arrive')).toBeInTheDocument();
    // Should show formatted time
    expect(screen.getByText(/Today by|by \d{2}:\d{2}/)).toBeInTheDocument();
  });

  it('does not show expected arrival time row when not supplied', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'completed',
      customer_visible_status: 'Sent',
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
        <PaymentSentPage />
      </BrowserRouter>
    );

    expect(screen.queryByText('Expected to arrive')).not.toBeInTheDocument();
    // Should show From account instead
    expect(screen.getByText('From')).toBeInTheDocument();
    expect(screen.getByText('Alice Murray')).toBeInTheDocument();
  });

  it('shows payment sent message', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'completed',
      customer_visible_status: 'Sent',
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
        <PaymentSentPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Your payment of £250\.00 to K Evans Lettings has been sent/)).toBeInTheDocument();
  });

  it('shows payment details with correct formatting', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'completed',
      customer_visible_status: 'Sent',
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
        <PaymentSentPage />
      </BrowserRouter>
    );

    // Check all required details are shown
    expect(screen.getByText('To')).toBeInTheDocument();
    expect(screen.getAllByText('K Evans Lettings')[0]).toBeInTheDocument();
    expect(screen.getByText('Amount')).toBeInTheDocument();
    expect(screen.getByText('£250.00')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('renders action buttons', () => {
    const mockPayment = {
      payment_id: 'pay-001',
      current_state: 'completed',
      customer_visible_status: 'Sent',
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
        <PaymentSentPage />
      </BrowserRouter>
    );

    expect(screen.getByRole('button', { name: /back to accounts/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /make another payment/i })).toBeInTheDocument();
  });
});
