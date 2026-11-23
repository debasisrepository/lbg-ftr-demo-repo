import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { PaymentEntryPage } from '../pages/PaymentEntryPage';
import * as authContext from '../lib/auth-context';
import * as apiClient from '../lib/api-client';

const mockNavigate = vi.fn();
const mockLocation = {
  pathname: '/payment-entry',
  state: {
    payee: {
      payee_id: '1',
      payee_name: 'K Evans Lettings',
      payee_sort_code: '20-45-77',
      masked_account_identifier: '****9842',
    },
  },
  search: '',
  hash: '',
  key: 'default',
};

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => mockLocation,
  };
});

vi.spyOn(authContext, 'useAuth').mockReturnValue({
  isAuthenticated: true,
  user: { display_name: 'Alex Taylor' },
  login: vi.fn(),
  logout: vi.fn(),
  isLoading: false,
});

describe('PaymentEntryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.setItem('auth_token', 'test-token');
  });

  it('renders payment entry form with payee details', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockResolvedValue({
      items: [
        {
          account_id: '1',
          account_type: 'current',
          display_name: 'Current Account',
          masked_account_identifier: '****5920',
          balance: {
            availability_state: 'current',
            amount_minor: 124836,
            currency: 'GBP',
            display_text: '£1,248.36',
          },
          as_of_timestamp: '2026-11-22T10:30:00Z',
          freshness_status: 'within_target',
          freshness_text: 'Updated moments ago',
          item_state: 'available',
          payment_source_eligible: true,
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(
      <BrowserRouter>
        <PaymentEntryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Pay K Evans Lettings')).toBeInTheDocument();
      expect(screen.getByText(/Sort code 20-45-77, account ending \*\*\*\*9842/)).toBeInTheDocument();
      expect(screen.getByLabelText('From')).toBeInTheDocument();
      expect(screen.getByLabelText(/Amount/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Payment reference/)).toBeInTheDocument();
    });
  });

  it('disables submit button when form is incomplete', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockResolvedValue({
      items: [
        {
          account_id: '1',
          account_type: 'current',
          display_name: 'Current Account',
          masked_account_identifier: '****5920',
          balance: {
            availability_state: 'current',
            amount_minor: 124836,
            currency: 'GBP',
            display_text: '£1,248.36',
          },
          payment_source_eligible: true,
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(
      <BrowserRouter>
        <PaymentEntryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Pay K Evans Lettings')).toBeInTheDocument();
    });

    const submitButton = screen.getByRole('button', { name: /Review payment/i });
    
    // Button should be disabled when form is empty
    expect(submitButton).toBeDisabled();
    
    // Check hint text explaining why button is disabled
    expect(screen.getByText(/The button stays off until the source account, amount and reference are complete/)).toBeInTheDocument();
  });

  it('submits payment when form is complete', async () => {
    const user = userEvent.setup();
    
    vi.spyOn(apiClient.apiClient, 'get').mockResolvedValue({
      items: [
        {
          account_id: 'acc-1',
          account_type: 'current',
          display_name: 'Current Account',
          masked_account_identifier: '****5920',
          balance: {
            availability_state: 'current',
            amount_minor: 124836,
            currency: 'GBP',
            display_text: '£1,248.36',
          },
          payment_source_eligible: true,
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    });

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        payment_id: 'pay-1',
        current_state: 'review_ready',
        next_action: 'review_and_approve',
        customer_visible_status: null,
        status_message: 'Payment not sent yet',
        is_submitted: false,
        do_not_resubmit: false,
        payment_reference: 'Invoice 2041',
        amount_minor: 25000,
        currency: 'GBP',
        source_account: {
          account_id: 'acc-1',
          display_name: 'Current Account',
          masked_account_identifier: '****5920',
        },
        payee: {
          payee_id: '1',
          payee_name: 'K Evans Lettings',
          masked_account_identifier: '****9842',
        },
        review_version: 1,
        review_fingerprint: 'abc123',
        created_at: '2026-11-22T12:00:00Z',
        updated_at: '2026-11-22T12:00:00Z',
      }),
    });

    render(
      <BrowserRouter>
        <PaymentEntryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Pay K Evans Lettings')).toBeInTheDocument();
    });

    const amountInput = screen.getByLabelText(/Amount/);
    const referenceInput = screen.getByLabelText(/Payment reference/);
    
    await user.clear(amountInput);
    await user.type(amountInput, '250.00');
    
    await user.clear(referenceInput);
    await user.type(referenceInput, 'Invoice 2041');

    const submitButton = screen.getByRole('button', { name: /Review payment/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/payment-review', expect.objectContaining({
        state: expect.objectContaining({
          payment: expect.objectContaining({
            payment_id: 'pay-1',
            payment_reference: 'Invoice 2041',
          }),
        }),
      }));
    });
  });

  it('filters accounts to show only payment_source_eligible accounts', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockResolvedValue({
      items: [
        {
          account_id: '1',
          display_name: 'Current Account',
          masked_account_identifier: '****5920',
          payment_source_eligible: true,
          balance: { display_text: '£1,248.36' },
        },
        {
          account_id: '2',
          display_name: 'Stale Account',
          masked_account_identifier: '****9012',
          payment_source_eligible: false,
          balance: { display_text: 'Balance unavailable' },
        },
      ],
      total: 2,
      page: 1,
      page_size: 20,
    });

    render(
      <BrowserRouter>
        <PaymentEntryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      const select = screen.getByLabelText('From') as HTMLSelectElement;
      expect(select.options).toHaveLength(1);
      expect(select.options[0].text).toContain('Current Account');
      expect(select.options[0].text).not.toContain('Stale Account');
    });
  });

  it('shows unavailable balance text correctly', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockResolvedValue({
      items: [
        {
          account_id: '1',
          display_name: 'Savings Account',
          masked_account_identifier: '****4417',
          payment_source_eligible: true,
          balance: {
            availability_state: 'unavailable',
            amount_minor: null,
            currency: null,
            display_text: 'Balance unavailable',
          },
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(
      <BrowserRouter>
        <PaymentEntryPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      const select = screen.getByLabelText('From') as HTMLSelectElement;
      expect(select.options[0].text).toContain('Balance unavailable');
      expect(select.options[0].text).not.toContain('£0.00');
    });
  });
});
