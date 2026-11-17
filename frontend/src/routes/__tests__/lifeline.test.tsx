import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { LifelinePage } from '../lifeline';
import { AuthProvider } from '../../lib/auth-context';
import * as apiClient from '../../lib/api-client';

// Mock the API client
vi.mock('../../lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

const mockLifelineData = {
  guidance_items: [
    {
      id: 'g1',
      incident_reference: 'INC-001',
      guidance_category: 'what_still_works',
      guidance_title: 'Cash machines',
      guidance_body: 'You can still take out cash with your card and PIN.',
      published_at: '2024-01-01T10:00:00Z',
    },
    {
      id: 'g2',
      incident_reference: 'INC-001',
      guidance_category: 'what_is_affected',
      guidance_title: 'Card payments in shops',
      guidance_body: 'Some payments are slow and a few may be declined.',
      published_at: '2024-01-01T10:00:00Z',
    },
    {
      id: 'g3',
      incident_reference: 'INC-001',
      guidance_category: 'protective_action',
      guidance_title: 'Keep another way to pay',
      guidance_body: 'Carry a little cash or a second payment method if you can.',
      published_at: '2024-01-01T10:00:00Z',
    },
  ],
  protective_actions: ['Keep another way to pay', 'Do not share security details'],
  fallback_channels: [
    {
      channel_type: 'phone',
      label: 'Phone',
      contact_detail: '0800123456',
      availability_text: 'Open 24 hours',
    },
    {
      channel_type: 'callback',
      label: 'Ask for a call back',
      contact_detail: null,
      availability_text: 'We will ring you when a colleague is free',
    },
  ],
  cache_version: 'v1',
  cache_age_seconds: 0,
  generated_at: '2024-01-01T12:00:00Z',
  withdrawn_cache_versions: [],
};

describe('LifelinePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders loading state initially', () => {
    vi.mocked(apiClient.apiClient.get).mockImplementation(() => new Promise(() => {}));
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <LifelinePage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    expect(screen.getByText(/Loading guidance/i)).toBeInTheDocument();
  });

  it('renders lifeline guidance when loaded successfully', async () => {
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(mockLifelineData);
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <LifelinePage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/What you can do now/i)).toBeInTheDocument();
    });
    
    expect(screen.getByText(/What still works/i)).toBeInTheDocument();
    expect(screen.getByText(/What is affected/i)).toBeInTheDocument();
    expect(screen.getByText(/Protect yourself/i)).toBeInTheDocument();
    expect(screen.getByText(/Ways to reach us/i)).toBeInTheDocument();
  });

  it('displays guidance items grouped by category', async () => {
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(mockLifelineData);
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <LifelinePage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Cash machines')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Card payments in shops')).toBeInTheDocument();
    expect(screen.getByText('Keep another way to pay')).toBeInTheDocument();
  });

  it('displays fallback channels', async () => {
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(mockLifelineData);
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <LifelinePage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Phone')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Ask for a call back')).toBeInTheDocument();
    expect(screen.getByText('Open 24 hours')).toBeInTheDocument();
  });

  it('displays phone link for talking to a person', async () => {
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(mockLifelineData);
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <LifelinePage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      const talkButton = screen.getByText(/Talk to a person/i);
      expect(talkButton).toBeInTheDocument();
      expect(talkButton.closest('a')).toHaveAttribute('href', 'tel:0800123456');
    });
  });

  it('falls back to cached data when API fails', async () => {
    // Set up cached data
    localStorage.setItem(
      'clearpath_lifeline_cache',
      JSON.stringify(mockLifelineData)
    );
    
    vi.mocked(apiClient.apiClient.get).mockRejectedValue(new Error('Network error'));
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <LifelinePage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/Showing saved guidance/i)).toBeInTheDocument();
    });
    
    expect(screen.getByText(/What you can do now/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Try again/i })).toBeInTheDocument();
  });

  it('allows retrying when using cached data', async () => {
    localStorage.setItem(
      'clearpath_lifeline_cache',
      JSON.stringify(mockLifelineData)
    );
    
    vi.mocked(apiClient.apiClient.get).mockRejectedValueOnce(new Error('Network error'));
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <LifelinePage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Try again/i })).toBeInTheDocument();
    });
    
    // Click retry button
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(mockLifelineData);
    fireEvent.click(screen.getByRole('button', { name: /Try again/i }));
    
    await waitFor(() => {
      expect(screen.queryByText(/Showing saved guidance/i)).not.toBeInTheDocument();
    });
  });

  it('shows error when API fails and no cache available', async () => {
    vi.mocked(apiClient.apiClient.get).mockRejectedValue(new Error('Network error'));
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <LifelinePage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/Could not load lifeline guidance/i)).toBeInTheDocument();
    });
  });

  it('has back link to service status', async () => {
    vi.mocked(apiClient.apiClient.get).mockResolvedValue(mockLifelineData);
    
    render(
      <BrowserRouter>
        <AuthProvider>
          <LifelinePage />
        </AuthProvider>
      </BrowserRouter>
    );
    
    await waitFor(() => {
      const backLink = screen.getByRole('link', { name: /Service status/i });
      expect(backLink).toHaveAttribute('href', '/status');
    });
  });
});
