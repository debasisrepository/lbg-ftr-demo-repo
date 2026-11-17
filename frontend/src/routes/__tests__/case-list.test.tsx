import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { CaseListPage } from '../case-list';
import * as useResourceModule from '../../hooks/use-resource';

vi.mock('../../hooks/use-resource');

const mockUseCases = vi.fn();
const mockUseStatus = vi.fn();
const mockUseNotifications = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  (useResourceModule.useCases as any) = mockUseCases;
  (useResourceModule.useStatus as any) = mockUseStatus;
  (useResourceModule.useNotifications as any) = mockUseNotifications;
});

describe('CaseListPage', () => {
  it('renders My Cases heading', () => {
    mockUseCases.mockReturnValue({ data: { items: [] }, loading: false, error: null });
    mockUseStatus.mockReturnValue({ data: null });
    mockUseNotifications.mockReturnValue({ data: { items: [] } });

    render(
      <BrowserRouter>
        <CaseListPage />
      </BrowserRouter>
    );

    expect(screen.getByText('My Cases')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    mockUseCases.mockReturnValue({ data: null, loading: true, error: null });
    mockUseStatus.mockReturnValue({ data: null });
    mockUseNotifications.mockReturnValue({ data: { items: [] } });

    render(
      <BrowserRouter>
        <CaseListPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Loading cases...')).toBeInTheDocument();
  });

  it('displays error state', () => {
    mockUseCases.mockReturnValue({ data: null, loading: false, error: 'Failed to load' });
    mockUseStatus.mockReturnValue({ data: null });
    mockUseNotifications.mockReturnValue({ data: { items: [] } });

    render(
      <BrowserRouter>
        <CaseListPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Failed to load')).toBeInTheDocument();
  });

  it('renders case tiles with data', async () => {
    const mockCases = {
      items: [
        {
          case_reference: 'CP-12345',
          issue_title: 'Test Issue',
          issue_type: 'card_declined',
          current_lifecycle_state: 'case_created',
          status_code: 'received',
          status_label: 'Received',
          latest_meaningful_update_text: 'Case received',
          latest_meaningful_update_at: '2024-01-01T12:00:00Z',
          owner: {
            owner_team_code: 'TEAM1',
            owner_semantic_label: 'Team One',
            owner_display_name: 'Support Team',
            effective_from: '2024-01-01T00:00:00Z',
          },
          expected_by: {
            commitment_state: 'under_review',
            expected_by_at: null,
            customer_explanatory_text: 'Timing is under review',
            confidence_basis: 'initial',
            effective_from: '2024-01-01T00:00:00Z',
          },
          opened_at: '2024-01-01T10:00:00Z',
          closed_at: null,
          outcome_summary: null,
        },
      ],
    };

    mockUseCases.mockReturnValue({ data: mockCases, loading: false, error: null });
    mockUseStatus.mockReturnValue({ data: null });
    mockUseNotifications.mockReturnValue({ data: { items: [] } });

    render(
      <BrowserRouter>
        <CaseListPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Test Issue')).toBeInTheDocument();
    });

    expect(screen.getByText(/CP-12345/)).toBeInTheDocument();
    expect(screen.getByText('Received')).toBeInTheDocument();
    expect(screen.getByText('Support Team')).toBeInTheDocument();
  });

  it('displays status banner when incidents exist', () => {
    const mockStatus = {
      status_state: 'disruption' as const,
      incidents: [
        {
          incident_reference: 'INC-001',
          incident_state: 'active',
          affected_service_code: 'CARDS',
          customer_impact_summary: 'Some card payments are slower than usual',
        },
      ],
      lifeline_available: true,
      cache_version: 'v1',
      generated_at: '2024-01-01T12:00:00Z',
    };

    mockUseCases.mockReturnValue({ data: { items: [] }, loading: false, error: null });
    mockUseStatus.mockReturnValue({ data: mockStatus });
    mockUseNotifications.mockReturnValue({ data: { items: [] } });

    render(
      <BrowserRouter>
        <CaseListPage />
      </BrowserRouter>
    );

    expect(screen.getByText('Some card payments are slower than usual')).toBeInTheDocument();
  });
});
