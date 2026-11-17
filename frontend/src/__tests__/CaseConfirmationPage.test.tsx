import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { CaseConfirmationPage } from '../pages/CaseConfirmationPage';
import { apiClient } from '../lib/api-client';

vi.mock('../lib/api-client');

const mockApiClient = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>;
};

describe('CaseConfirmationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    mockApiClient.get.mockImplementation(() => new Promise(() => {}));
    
    render(
      <BrowserRouter>
        <CaseConfirmationPage />
      </BrowserRouter>
    );
    
    expect(screen.getByRole('status')).toHaveTextContent(/loading/i);
  });

  it('renders case confirmation with hero and three-panel sections', async () => {
    const mockCaseDetail = {
      id: 'case-123',
      case_ref: 'CP-2024-001234',
      customer_user_id: 'user-123',
      status: 'new',
      problem_statement: 'Unrecognised payment of £89.99',
      classification: 'fraud_report',
      owner_team_display: 'Card fraud team',
      expected_by_at: new Date(Date.now() + 3600000).toISOString(),
      last_update_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      route_reason: 'Customer requested human assistance'
    };

    const mockCasesList = {
      items: [mockCaseDetail],
      total: 1
    };

    mockApiClient.get.mockImplementation((path: string) => {
      if (path.includes('/cases/case-123')) {
        return Promise.resolve(mockCaseDetail);
      }
      if (path.includes('/cases?')) {
        return Promise.resolve(mockCasesList);
      }
      return Promise.reject(new Error('Unknown path'));
    });

    // Mock URLSearchParams
    delete (window as { location?: unknown }).location;
    window.location = { search: '?caseId=case-123' } as Location;

    render(
      <BrowserRouter>
        <CaseConfirmationPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("We've passed this to our team")).toBeInTheDocument();
    });

    expect(screen.getByText(/What you need to know/i)).toBeInTheDocument();
    expect(screen.getByText(/Who has it/i)).toBeInTheDocument();
    expect(screen.getByText(/Next update expected by/i)).toBeInTheDocument();
  });

  it('renders My Cases list with new case highlighted', async () => {
    const mockCaseDetail = {
      id: 'case-123',
      case_ref: 'CP-2024-001234',
      customer_user_id: 'user-123',
      status: 'new',
      problem_statement: 'Unrecognised payment',
      owner_team_display: 'Card fraud team',
      expected_by_at: new Date(Date.now() + 3600000).toISOString(),
      last_update_at: new Date().toISOString(),
      created_at: new Date().toISOString()
    };

    const mockCasesList = {
      items: [
        mockCaseDetail,
        {
          ...mockCaseDetail,
          id: 'case-456',
          case_ref: 'CP-2024-001235',
          status: 'waiting_for_customer'
        }
      ],
      total: 2
    };

    mockApiClient.get.mockImplementation((path: string) => {
      if (path.includes('/cases/case-123')) {
        return Promise.resolve(mockCaseDetail);
      }
      if (path.includes('/cases?')) {
        return Promise.resolve(mockCasesList);
      }
      return Promise.reject(new Error('Unknown path'));
    });

    delete (window as { location?: unknown }).location;
    window.location = { search: '?caseId=case-123' } as Location;

    render(
      <BrowserRouter>
        <CaseConfirmationPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Now in My Cases/i)).toBeInTheDocument();
    });

    // Find by text content function since "Case CP-2024-001234" is split
    expect(screen.getByText((content, element) => {
      return element?.textContent === 'Case CP-2024-001234 · New';
    })).toBeInTheDocument();
    expect(screen.getByText('2 open')).toBeInTheDocument();
  });

  it('renders error state when case fetch fails', async () => {
    mockApiClient.get.mockRejectedValue(new Error('Failed to fetch case'));

    delete (window as { location?: unknown }).location;
    window.location = { search: '?caseId=case-123' } as Location;

    render(
      <BrowserRouter>
        <CaseConfirmationPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/failed to fetch case/i);
    });
  });

  it('renders action buttons', async () => {
    const mockCaseDetail = {
      id: 'case-123',
      case_ref: 'CP-2024-001234',
      customer_user_id: 'user-123',
      status: 'new',
      problem_statement: 'Test case',
      expected_by_at: new Date(Date.now() + 3600000).toISOString(),
      last_update_at: new Date().toISOString(),
      created_at: new Date().toISOString()
    };

    mockApiClient.get.mockImplementation((path: string) => {
      if (path.includes('/cases/case-123')) {
        return Promise.resolve(mockCaseDetail);
      }
      if (path.includes('/cases?')) {
        return Promise.resolve({ items: [mockCaseDetail], total: 1 });
      }
      return Promise.reject(new Error('Unknown path'));
    });

    delete (window as { location?: unknown }).location;
    window.location = { search: '?caseId=case-123' } as Location;

    render(
      <BrowserRouter>
        <CaseConfirmationPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("We've passed this to our team")).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /Open the conversation/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /I'd like a call-back/i })).toBeInTheDocument();
  });
});
