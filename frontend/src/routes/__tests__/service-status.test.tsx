import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ServiceStatusPage } from '../service-status';
import { AuthProvider } from '../../lib/auth-context';
import * as apiClient from '../../lib/api-client';

// Mock the API client
vi.mock('../../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

const mockOperationalStatus = {
  status_state: 'operational' as const,
  incidents: [],
  lifeline_available: false,
  generated_at: '2024-01-01T12:00:00Z',
  cache_version: 'v1',
  max_age_seconds: 60,
};

const mockDisruptionStatus = {
  status_state: 'disruption' as const,
  incidents: [
    {
      incident_reference: 'INC-001',
      incident_state: 'declared',
      affected_service_code: 'card_payments',
      customer_impact_summary: 'Card payments slower than usual',
      started_at: '2024-01-01T10:00:00Z',
      resolved_at: null,
      publications: [
        {
          headline_text: 'Card payment issues',
          summary_text: 'Some card payments are taking longer',
          affected_journeys: ['card_payment', 'atm_withdrawal'],
          published_at: '2024-01-01T10:00:00Z',
        },
      ],
    },
  ],
  lifeline_available: true,
  generated_at: '2024-01-01T12:00:00Z',
  cache_version: 'v2',
  max_age_seconds: 60,
};

describe('ServiceStatusPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(apiClient.apiClient.get).mockImplementation(() => new Promise(() => {}));
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <ServiceStatusPage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    expect(screen.getByText(/Loading service status/i)).toBeInTheDocument();
  });

  it('renders operational status when no incidents', async () => {
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(mockOperationalStatus);
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <ServiceStatusPage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/Everything is working/i)).toBeInTheDocument();
    });
    
    expect(screen.getByText(/not aware of any problems/i)).toBeInTheDocument();
  });

  it('renders incidents when disruption exists', async () => {
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(mockDisruptionStatus);
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <ServiceStatusPage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/Happening now/i)).toBeInTheDocument();
    });
    
    expect(screen.getByText(/Card payment issues/i)).toBeInTheDocument();
    expect(screen.getByText(/Some card payments are taking longer/i)).toBeInTheDocument();
  });

  it('shows lifeline button when available during disruption', async () => {
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(mockDisruptionStatus);
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <ServiceStatusPage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/See what you can do now/i)).toBeInTheDocument();
    });
  });

  it('renders error state when fetch fails', async () => {
    vi.mocked(apiClient.apiClient.get).mockRejectedValue(new Error('Network error'));
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <ServiceStatusPage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });
  });

  it('displays last updated timestamp', async () => {
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(mockOperationalStatus);
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <ServiceStatusPage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/Last updated/i)).toBeInTheDocument();
    });
  });
});
