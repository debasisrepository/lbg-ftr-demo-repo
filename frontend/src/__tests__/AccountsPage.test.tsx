import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AccountsPage from '../pages/AccountsPage';
import * as apiClient from '../lib/api-client';
import * as authContext from '../lib/auth-context';

vi.mock('../lib/api-client');
vi.mock('../lib/auth-context');

const mockAccountsResponse = {
  profile: {
    profile_id: 1,
    profile_type: 'personal',
    display_name: 'John Smith',
    business_name: null,
    can_view_accounts: true,
    can_create_payee: true,
    can_approve_payment: true,
  },
  accounts: [
    {
      account_id: 1,
      account_type: 'current_account',
      account_name: 'Current Account',
      masked_account_number: '****5678',
      sort_code: '00-03-20',
      currency: 'GBP',
      current_balance_minor: 124836,
      available_balance_minor: 124836,
      overdraft_available_minor: 100000,
      freshness_state: 'current',
      last_updated_at: '2026-11-19T10:00:00Z',
    },
  ],
  data_gaps: [],
};

const mockAuthContext = {
  user: { id: 1, username: 'testuser', status: 'active' },
  token: 'mock-token-123',
  activeProfileId: 2,
  isAuthenticated: true,
  login: vi.fn(),
  logout: vi.fn(),
  loading: false,
};

describe('AccountsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(authContext.useAuth).mockReturnValue(mockAuthContext);
  });

  it('renders without crashing', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockAccountsResponse);

    const { container } = render(
      <BrowserRouter>
        <AccountsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(container).toBeTruthy();
    });
  });

  it('shows loading state initially', () => {
    vi.mocked(apiClient.get).mockImplementation(() => new Promise(() => {}));

    render(
      <BrowserRouter>
        <AccountsPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Loading accounts...')).toBeInTheDocument();
  });

  it('shows error state on failure', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'));

    render(
      <BrowserRouter>
        <AccountsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Error loading accounts')).toBeInTheDocument();
    });
  });

  it('fetches accounts from API', async () => {
    const getSpy = vi.mocked(apiClient.get).mockResolvedValue(mockAccountsResponse);

    render(
      <BrowserRouter>
        <AccountsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(getSpy).toHaveBeenCalledWith('/accounts/overview?profile_id=2');
    });
  });

  it('renders profile badge', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockAccountsResponse);

    render(
      <BrowserRouter>
        <AccountsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Active profile:/i)).toBeInTheDocument();
    });
  });

  it('renders account information', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockAccountsResponse);

    render(
      <BrowserRouter>
        <AccountsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Current Account')).toBeInTheDocument();
    });
  });
});
