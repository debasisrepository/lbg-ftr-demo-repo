import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ProtectedActionPage } from '../case-action';
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

describe('ProtectedActionPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads and displays protected action with pending_sca status', async () => {
    vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce({
      action_id: '00000000-0000-0000-0000-000000014001',
      action_type: 'stop_card',
      action_domain: 'card',
      request_status: 'pending_sca',
      sca_outcome: 'not_invoked',
      sca_invoked_at: '2024-01-15T10:00:00Z',
      sca_completed_at: null,
      management_api_reference: null,
      fallback_guidance_text: null,
      completed_at: null,
      created_at: '2024-01-15T10:00:00Z',
    });

    render(
      <MemoryRouter initialEntries={['/cases/CP-MOCK1/actions/00000000-0000-0000-0000-000000014001']}>
        <Routes>
          <Route path="/cases/:caseReference/actions/:actionId" element={<ProtectedActionPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Protected action' })).toBeInTheDocument();
    });

    expect(screen.getByText(/This action requires security verification/)).toBeInTheDocument();
  });

  it('displays SCA prompt for pending_sca status', async () => {
    vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce({
      action_id: '00000000-0000-0000-0000-000000014001',
      action_type: 'stop_card',
      action_domain: 'card',
      request_status: 'pending_sca',
      sca_outcome: 'not_invoked',
      sca_invoked_at: '2024-01-15T10:00:00Z',
      sca_completed_at: null,
      management_api_reference: null,
      fallback_guidance_text: null,
      completed_at: null,
      created_at: '2024-01-15T10:00:00Z',
    });

    render(
      <MemoryRouter initialEntries={['/cases/CP-MOCK1/actions/00000000-0000-0000-0000-000000014001']}>
        <Routes>
          <Route path="/cases/:caseReference/actions/:actionId" element={<ProtectedActionPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Security check required' })).toBeInTheDocument();
    });

    expect(screen.getByText(/Confirm in your banking app/)).toBeInTheDocument();
  });

  it('displays success outcome when action is released', async () => {
    vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce({
      action_id: '00000000-0000-0000-0000-000000014001',
      action_type: 'stop_card',
      action_domain: 'card',
      request_status: 'released',
      sca_outcome: 'success',
      sca_invoked_at: '2024-01-15T10:00:00Z',
      sca_completed_at: '2024-01-15T10:05:00Z',
      management_api_reference: 'MGMT-card-stop_card-123',
      fallback_guidance_text: null,
      completed_at: '2024-01-15T10:05:00Z',
      created_at: '2024-01-15T10:00:00Z',
    });

    render(
      <MemoryRouter initialEntries={['/cases/CP-MOCK1/actions/00000000-0000-0000-0000-000000014001']}>
        <Routes>
          <Route path="/cases/:caseReference/actions/:actionId" element={<ProtectedActionPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Security check passed')).toBeInTheDocument();
    });

    expect(screen.getByText(/Your request has been processed/)).toBeInTheDocument();
    expect(screen.getByText(/MGMT-card-stop_card-123/)).toBeInTheDocument();
  });

  it('displays fallback guidance when action is not_executed', async () => {
    vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce({
      action_id: '00000000-0000-0000-0000-000000014001',
      action_type: 'stop_card',
      action_domain: 'card',
      request_status: 'not_executed',
      sca_outcome: 'failed',
      sca_invoked_at: '2024-01-15T10:00:00Z',
      sca_completed_at: '2024-01-15T10:05:00Z',
      management_api_reference: null,
      fallback_guidance_text: 'Please call us immediately on 0345 300 0000 to secure your account.',
      completed_at: '2024-01-15T10:05:00Z',
      created_at: '2024-01-15T10:00:00Z',
    });

    render(
      <MemoryRouter initialEntries={['/cases/CP-MOCK1/actions/00000000-0000-0000-0000-000000014001']}>
        <Routes>
          <Route path="/cases/:caseReference/actions/:actionId" element={<ProtectedActionPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Please call us immediately/)).toBeInTheDocument();
    });
  });

  it('handles action not found error', async () => {
    vi.mocked(apiClientModule.apiClient.get).mockRejectedValueOnce(
      new Error('Action not found')
    );

    render(
      <MemoryRouter initialEntries={['/cases/CP-MOCK1/actions/00000000-0000-0000-0000-999999999999']}>
        <Routes>
          <Route path="/cases/:caseReference/actions/:actionId" element={<ProtectedActionPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load action')).toBeInTheDocument();
    });

    expect(screen.getByText('Action not found')).toBeInTheDocument();
  });

  it('provides back link to case detail', async () => {
    vi.mocked(apiClientModule.apiClient.get).mockResolvedValueOnce({
      action_id: '00000000-0000-0000-0000-000000014001',
      action_type: 'stop_card',
      action_domain: 'card',
      request_status: 'pending_sca',
      sca_outcome: 'not_invoked',
      sca_invoked_at: '2024-01-15T10:00:00Z',
      sca_completed_at: null,
      management_api_reference: null,
      fallback_guidance_text: null,
      completed_at: null,
      created_at: '2024-01-15T10:00:00Z',
    });

    render(
      <MemoryRouter initialEntries={['/cases/CP-MOCK1/actions/00000000-0000-0000-0000-000000014001']}>
        <Routes>
          <Route path="/cases/:caseReference/actions/:actionId" element={<ProtectedActionPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Protected action' })).toBeInTheDocument();
    });

    const backLinks = screen.getAllByText(/Case CP-MOCK1/);
    // Find the one that is inside an anchor tag with class back-link
    const backLink = backLinks.find(link => link.closest('a')?.className.includes('back-link'));
    expect(backLink).toBeTruthy();
    expect(backLink?.closest('a')).toHaveAttribute('href', '/cases/CP-MOCK1');
  });
});
