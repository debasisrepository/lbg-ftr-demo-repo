import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { CaseHistoryPage } from '../case-history';
import * as apiClientModule from '../../lib/api-client';

vi.mock('../../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('CaseHistoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads and displays case history events', async () => {
    vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce({
      items: [
        {
          id: '1',
          sequence_number: 3,
          event_type: 'CaseStatusChanged',
          event_timestamp: '2024-01-15T10:30:00Z',
          summary_text: 'Status: In progress',
          customer_visible_flag: true,
          actor_type: 'system',
          actor_reference: null,
          basis_type: null,
          basis_reference: null,
          lifecycle_from: 'case_created',
          lifecycle_to: 'in_progress',
        },
        {
          id: '2',
          sequence_number: 2,
          event_type: 'OwnerChanged',
          event_timestamp: '2024-01-15T09:00:00Z',
          summary_text: 'Owner is now Cards support team',
          customer_visible_flag: true,
          actor_type: 'system',
          actor_reference: null,
          basis_type: null,
          basis_reference: null,
          lifecycle_from: null,
          lifecycle_to: null,
        },
        {
          id: '3',
          sequence_number: 1,
          event_type: 'CaseCaptured',
          event_timestamp: '2024-01-15T08:58:00Z',
          summary_text: 'We have your request',
          customer_visible_flag: true,
          actor_type: 'customer',
          actor_reference: null,
          basis_type: null,
          basis_reference: null,
          lifecycle_from: null,
          lifecycle_to: null,
        },
      ],
      total: 3,
      limit: 20,
      offset: 0,
    });

    render(
      <MemoryRouter initialEntries={['/cases/CP-12345/history']}>
        <Routes>
          <Route path="/cases/:caseReference/history" element={<CaseHistoryPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Case history')).toBeInTheDocument();
    });

    expect(screen.getByText('Status: In progress')).toBeInTheDocument();
    expect(screen.getByText('Owner is now Cards support team')).toBeInTheDocument();
    expect(screen.getByText('We have your request')).toBeInTheDocument();
    expect(screen.getByText('Showing 3 of 3 updates')).toBeInTheDocument();
  });

  it('displays superseded badge for duplicate event types', async () => {
    vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce({
      items: [
        {
          id: '1',
          sequence_number: 3,
          event_type: 'OwnerChanged',
          event_timestamp: '2024-01-15T10:00:00Z',
          summary_text: 'Owner is now Fraud team',
          customer_visible_flag: true,
          actor_type: 'system',
          actor_reference: null,
          basis_type: null,
          basis_reference: null,
          lifecycle_from: null,
          lifecycle_to: null,
        },
        {
          id: '2',
          sequence_number: 2,
          event_type: 'OwnerChanged',
          event_timestamp: '2024-01-15T09:00:00Z',
          summary_text: 'Owner is now Cards team',
          customer_visible_flag: true,
          actor_type: 'system',
          actor_reference: null,
          basis_type: null,
          basis_reference: null,
          lifecycle_from: null,
          lifecycle_to: null,
        },
      ],
      total: 2,
      limit: 20,
      offset: 0,
    });

    render(
      <MemoryRouter initialEntries={['/cases/CP-12345/history']}>
        <Routes>
          <Route path="/cases/:caseReference/history" element={<CaseHistoryPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Owner is now Fraud team')).toBeInTheDocument();
    });

    // The second (earlier) OwnerChanged event should have "Earlier" badge
    const supersededBadges = screen.getAllByText('Earlier');
    expect(supersededBadges.length).toBeGreaterThan(0);
  });

  it('shows load more button when there are more events', async () => {
    vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce({
      items: [
        {
          id: '1',
          sequence_number: 1,
          event_type: 'CaseCaptured',
          event_timestamp: '2024-01-15T08:58:00Z',
          summary_text: 'We have your request',
          customer_visible_flag: true,
          actor_type: 'customer',
          actor_reference: null,
          basis_type: null,
          basis_reference: null,
          lifecycle_from: null,
          lifecycle_to: null,
        },
      ],
      total: 5,
      limit: 1,
      offset: 0,
    });

    render(
      <MemoryRouter initialEntries={['/cases/CP-12345/history']}>
        <Routes>
          <Route path="/cases/:caseReference/history" element={<CaseHistoryPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Load more')).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    vi.mocked(apiClientModule.apiClient.get).mockRejectedValueOnce(new Error('Network error'));

    render(
      <MemoryRouter initialEntries={['/cases/CP-12345/history']}>
        <Routes>
          <Route path="/cases/:caseReference/history" element={<CaseHistoryPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load history')).toBeInTheDocument();
    });
  });

  it('shows empty state when no events exist', async () => {
    vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });

    render(
      <MemoryRouter initialEntries={['/cases/CP-12345/history']}>
        <Routes>
          <Route path="/cases/:caseReference/history" element={<CaseHistoryPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No history events found.')).toBeInTheDocument();
    });
  });
});
