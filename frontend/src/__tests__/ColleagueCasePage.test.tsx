import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ColleagueCasePage } from '../pages/ColleagueCasePage';
import { apiClient } from '../lib/api-client';

vi.mock('../lib/api-client');

const mockApiClient = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
};

describe('ColleagueCasePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    mockApiClient.get.mockImplementation(() => new Promise(() => {}));
    
    render(
      <MemoryRouter initialEntries={['/colleague/cases/case-123']}>
        <Routes>
          <Route path="/colleague/cases/:caseId" element={<ColleagueCasePage />} />
        </Routes>
      </MemoryRouter>
    );
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('renders colleague case with case header', async () => {
    const mockHandoffPack = {
      case_id: 'case-123',
      case_ref: 'CP-2024-001234',
      status_code: 'investigating',
      problem_statement: 'Unrecognised card payment',
      classification_code: 'fraud_report',
      route_reason: 'Customer requested human assistance',
      arrival_source: 'Assistant escalation',
      expected_by_at: new Date(Date.now() + 3600000).toISOString(),
      owner_team_display: 'Card fraud team',
      owner_colleague_display: 'Not yet picked up',
      handoff_summary_text: 'Customer reported unrecognised payment of £89.99',
      copilot_note: 'Check merchant history before responding',
      customer_display_name: 'Sam Okafor',
      brand: 'Lloyds',
      opened_at: new Date().toISOString()
    };

    const mockThread = {
      entries: [
        {
          entry_id: 'entry-1',
          role: 'customer',
          content_text: 'I have an unrecognised payment',
          visibility_scope: 'customer_and_colleague' as const,
          occurred_at: new Date().toISOString()
        }
      ],
      total: 1
    };

    mockApiClient.get.mockImplementation((path: string) => {
      if (path.includes('/colleague/cases/case-123/thread')) {
        return Promise.resolve(mockThread);
      }
      if (path.includes('/colleague/cases/case-123')) {
        return Promise.resolve(mockHandoffPack);
      }
      return Promise.reject(new Error('Unknown path'));
    });

    render(
      <MemoryRouter initialEntries={['/colleague/cases/case-123']}>
        <Routes>
          <Route path="/colleague/cases/:caseId" element={<ColleagueCasePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toBeInTheDocument();
    });

    // Case ref appears multiple times (breadcrumb, header), find first
    expect(screen.getAllByText(/CP-2024-001234/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/Unrecognised card payment/i)).toBeInTheDocument();
  });

  it('renders error state when case fetch fails', async () => {
    mockApiClient.get.mockRejectedValue(new Error('Failed to fetch case'));

    render(
      <MemoryRouter initialEntries={['/colleague/cases/case-123']}>
        <Routes>
          <Route path="/colleague/cases/:caseId" element={<ColleagueCasePage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to (fetch|load) case/i)).toBeInTheDocument();
    });
  });
});
