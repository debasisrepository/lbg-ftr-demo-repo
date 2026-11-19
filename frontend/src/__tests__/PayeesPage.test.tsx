import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import PayeesPage from '../pages/PayeesPage';
import * as apiClient from '../lib/api-client';
import * as authContext from '../lib/auth-context';

vi.mock('../lib/api-client');
vi.mock('../lib/auth-context');

const mockPayeesResponse = {
  payees: [
    {
      payee_id: 1,
      display_name: 'Jamie Clarke',
      sort_code: '04-00-04',
      masked_account_number: '****3746',
      nickname: null,
      can_proceed: true,
      latest_cop_result: 'match',
      latest_cop_checked_at: '2026-10-20T10:00:00Z',
    },
    {
      payee_id: 2,
      display_name: 'Priya Patel',
      sort_code: '08-92-99',
      masked_account_number: '****2178',
      nickname: null,
      can_proceed: true,
      latest_cop_result: 'match',
      latest_cop_checked_at: '2026-09-20T10:00:00Z',
    },
    {
      payee_id: 3,
      display_name: 'K Evans Lettings',
      sort_code: '20-45-77',
      masked_account_number: '****9842',
      nickname: null,
      can_proceed: true,
      latest_cop_result: 'match',
      latest_cop_checked_at: '2026-11-15T10:00:00Z',
    },
  ],
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

describe('PayeesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(authContext.useAuth).mockReturnValue(mockAuthContext);
  });

  it('AC1: renders payee list with saved payees', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockPayeesResponse);

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Jamie Clarke')).toBeInTheDocument();
      expect(screen.getByText('04-00-04 · ****3746')).toBeInTheDocument();
      expect(screen.getByText('Priya Patel')).toBeInTheDocument();
      expect(screen.getByText('K Evans Lettings')).toBeInTheDocument();
    });
  });

  it('AC2: allows selecting a saved payee', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockPayeesResponse);

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Jamie Clarke')).toBeInTheDocument();
    });

    const payeeTile = screen.getByRole('radio', { name: /Jamie Clarke/ });
    fireEvent.click(payeeTile);

    await waitFor(() => {
      expect(payeeTile).toHaveAttribute('aria-checked', 'true');
    });
  });

  it('AC3: enables Continue button when payee selected', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockPayeesResponse);

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Jamie Clarke')).toBeInTheDocument();
    });

    const continueButton = screen.getByRole('button', { name: /Continue to payment/i });
    expect(continueButton).toBeDisabled();

    const payeeTile = screen.getByRole('radio', { name: /Jamie Clarke/ });
    fireEvent.click(payeeTile);

    await waitFor(() => {
      expect(continueButton).not.toBeDisabled();
    });
  });

  it('AC4: shows Add a new payee button', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockPayeesResponse);

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Add a new payee')).toBeInTheDocument();
    });
  });

  it('AC5: shows new payee form when Add clicked', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockPayeesResponse);

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Add a new payee')).toBeInTheDocument();
    });

    const addButton = screen.getByText('Add a new payee');
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText('Fresh verification required')).toBeInTheDocument();
      expect(screen.getByLabelText('Name on the account')).toBeInTheDocument();
      expect(screen.getByLabelText('Sort code')).toBeInTheDocument();
      expect(screen.getByLabelText('Account number')).toBeInTheDocument();
    });
  });

  it('AC6: renders payee tiles in radio group', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(mockPayeesResponse);

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      const radioGroup = screen.getByRole('radiogroup', { name: /Saved payees/i });
      expect(radioGroup).toBeInTheDocument();
      
      const radioButtons = screen.getAllByRole('radio');
      expect(radioButtons.length).toBe(3);
    });
  });

  it('handles loading state', () => {
    vi.mocked(apiClient.get).mockImplementation(() => new Promise(() => {}));

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Loading payees...')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'));

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Error loading payees')).toBeInTheDocument();
    });
  });

  it('handles empty payee list', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ payees: [] });

    render(
      <BrowserRouter>
        <PayeesPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Add a new payee')).toBeInTheDocument();
    });
  });
});
