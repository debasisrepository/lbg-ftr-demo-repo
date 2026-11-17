import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { CaseDetailPage } from '../case-detail';
import { AuthProvider } from '../../lib/auth-context';
import * as apiClient from '../../lib/api-client';

// Mock the API client
vi.mock('../../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

const mockCase = {
  case_reference: 'CP-MOCK1',
  issue_type: 'card_declined',
  issue_title: 'Card payment declined',
  current_lifecycle_state: 'case_created',
  status_code: 'received',
  status_label: 'Received',
  latest_meaningful_update_text: 'Your case has been received',
  latest_meaningful_update_at: '2024-01-01T12:00:00Z',
  owner: {
    owner_team_code: 'INTAKE_DEFAULT',
    owner_semantic_label: 'Intake Team',
    owner_display_name: 'Intake & Triage',
    effective_from: '2024-01-01T12:00:00Z',
  },
  expected_by: {
    commitment_state: 'under_review',
    expected_by_at: null,
    customer_explanatory_text: 'We are reviewing the timing',
    confidence_basis: 'initial',
    effective_from: '2024-01-01T12:00:00Z',
  },
  opened_at: '2024-01-01T12:00:00Z',
  closed_at: null,
  outcome_summary: null,
  customer_party_id: 'CUST-002',
  brand: 'lloyds',
  classification_source: 'customer',
  issue_summary: 'Card declined at shop',
  origin_channel: 'mobile_app',
  status_summary_text: 'We are checking your payment',
  next_step_text: 'We will update you when we know more',
  outage_impact_banner_text: null,
  continuity_state: 'current',
};

function renderWithRouter(caseReference: string) {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/cases/:caseReference" element={<CaseDetailPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>,
    { wrapper: ({ children }) => <BrowserRouter><Routes><Route path="*" element={children} /></Routes></BrowserRouter> }
  );
}

describe('CaseDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(apiClient.apiClient.get).mockImplementation(() => new Promise(() => {}));
    
    window.history.pushState({}, '', '/cases/CP-MOCK1');
    render(
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/cases/:caseReference" element={<CaseDetailPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    );
    
    expect(screen.getByText(/Loading case details/i)).toBeInTheDocument();
  });

  it('renders case details when loaded successfully', async () => {
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(mockCase);
    
    window.history.pushState({}, '', '/cases/CP-MOCK1');
    render(
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/cases/:caseReference" element={<CaseDetailPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Card payment declined')).toBeInTheDocument();
    });
    
    expect(screen.getByText(/Case CP-MOCK1/i)).toBeInTheDocument();
    expect(screen.getByText('Intake & Triage')).toBeInTheDocument();
    expect(screen.getByText(/under review/i)).toBeInTheDocument();
  });

  it('renders outage banner when present', async () => {
    const caseWithOutage = {
      ...mockCase,
      outage_impact_banner_text: 'Service disruption may affect this case',
    };
    
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(caseWithOutage);
    
    window.history.pushState({}, '', '/cases/CP-MOCK1');
    render(
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/cases/:caseReference" element={<CaseDetailPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/outage may slow/i)).toBeInTheDocument();
    });
  });

  it('renders expected by date when available', async () => {
    const caseWithDate = {
      ...mockCase,
      expected_by: {
        ...mockCase.expected_by,
        expected_by_at: '2024-01-10T12:00:00Z',
      },
    };
    
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(caseWithDate);
    
    window.history.pushState({}, '', '/cases/CP-MOCK1');
    render(
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/cases/:caseReference" element={<CaseDetailPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/Expected by/i)).toBeInTheDocument();
    });
  });

  it('renders error state when fetch fails', async () => {
    vi.mocked(apiClient.apiClient.get).mockRejectedValue(new Error('Network error'));
    
    window.history.pushState({}, '', '/cases/CP-MOCK1');
    render(
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/cases/:caseReference" element={<CaseDetailPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });
  });
});
