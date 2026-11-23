import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { PayeesPage } from '../pages/PayeesPage';
import * as authContext from '../lib/auth-context';
import * as apiClient from '../lib/api-client';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ pathname: '/payees' }),
  };
});

const mockLogout = vi.fn();
vi.spyOn(authContext, 'useAuth').mockReturnValue({
  isAuthenticated: true,
  user: { display_name: 'Alex Taylor' },
  login: vi.fn(),
  logout: mockLogout,
  isLoading: false,
});

describe('PayeesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.spyOn(apiClient.apiClient, 'get').mockImplementation(() => new Promise(() => {}));
    
    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders payees list when loaded successfully', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockImplementation((path: string) => {
      if (path === '/v1/payees') {
        return Promise.resolve({
          items: [
            {
              payee_id: '1',
              payee_name: 'Jamie Clarke',
              payee_sort_code: '04-00-04',
              masked_account_identifier: '****3321',
            },
            {
              payee_id: '2',
              payee_name: 'Priya Patel',
              payee_sort_code: '60-83-71',
              masked_account_identifier: '****7745',
            },
          ],
          total: 2,
          page: 1,
          page_size: 20,
          capability: {
            capability_name: 'saved_payees',
            status_value: 'healthy',
            customer_message: 'Saved payees available',
            recovery_guidance: '',
            effective_from: '2026-11-22T10:30:00Z',
          },
        });
      }
      if (path === '/v1/capability-statuses/') {
        return Promise.resolve({
          items: [
            {
              capability_name: 'payments',
              status_value: 'healthy',
              customer_message: 'Payments available',
              recovery_guidance: '',
              effective_from: '2026-11-22T10:30:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 4,
        });
      }
      return Promise.reject(new Error('Unknown path'));
    });

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Jamie Clarke')).toBeInTheDocument();
      expect(screen.getByText('Priya Patel')).toBeInTheDocument();
      expect(screen.getByText(/Sort code 04-00-04, account ending \*\*\*\*3321/)).toBeInTheDocument();
    });
  });

  it('shows unavailable banner when saved_payees capability is unavailable', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockImplementation((path: string) => {
      if (path === '/v1/payees') {
        return Promise.resolve({
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          capability: {
            capability_name: 'saved_payees',
            status_value: 'unavailable',
            customer_message: 'Saved payees unavailable',
            recovery_guidance: 'Try again later',
            effective_from: '2026-11-22T10:30:00Z',
          },
        });
      }
      if (path === '/v1/capability-statuses/') {
        return Promise.resolve({
          items: [],
          total: 0,
          page: 1,
          page_size: 4,
        });
      }
      return Promise.reject(new Error('Unknown path'));
    });

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Your saved payees aren't available right now/)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Try again/i })).toBeInTheDocument();
    });
  });

  it('shows payments unavailable banner when payments capability is unavailable', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockImplementation((path: string) => {
      if (path === '/v1/payees') {
        return Promise.resolve({
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          capability: {
            capability_name: 'saved_payees',
            status_value: 'healthy',
            customer_message: 'Saved payees available',
            recovery_guidance: '',
            effective_from: '2026-11-22T10:30:00Z',
          },
        });
      }
      if (path === '/v1/capability-statuses/') {
        return Promise.resolve({
          items: [
            {
              capability_name: 'payments',
              status_value: 'unavailable',
              customer_message: 'Payments unavailable',
              recovery_guidance: 'Try again later',
              effective_from: '2026-11-22T10:30:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 4,
        });
      }
      return Promise.reject(new Error('Unknown path'));
    });

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/New payments are paused/)).toBeInTheDocument();
    });
  });

  it('navigates to payment entry when payee is selected', async () => {
    const user = userEvent.setup();
    
    vi.spyOn(apiClient.apiClient, 'get').mockImplementation((path: string) => {
      if (path === '/v1/payees') {
        return Promise.resolve({
          items: [
            {
              payee_id: '1',
              payee_name: 'Jamie Clarke',
              payee_sort_code: '04-00-04',
              masked_account_identifier: '****3321',
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
          capability: {
            capability_name: 'saved_payees',
            status_value: 'healthy',
            customer_message: 'Saved payees available',
            recovery_guidance: '',
            effective_from: '2026-11-22T10:30:00Z',
          },
        });
      }
      if (path === '/v1/capability-statuses/') {
        return Promise.resolve({
          items: [],
          total: 0,
          page: 1,
          page_size: 4,
        });
      }
      return Promise.reject(new Error('Unknown path'));
    });

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Jamie Clarke')).toBeInTheDocument();
    });

    const payeeButton = screen.getByRole('button', { name: /Jamie Clarke/i });
    await user.click(payeeButton);

    expect(mockNavigate).toHaveBeenCalledWith('/payment-entry', {
      state: {
        payee: {
          payee_id: '1',
          payee_name: 'Jamie Clarke',
          payee_sort_code: '04-00-04',
          masked_account_identifier: '****3321',
        },
      },
    });
  });
});
