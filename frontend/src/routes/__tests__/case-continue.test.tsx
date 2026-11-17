import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ContinueChannelPage } from '../case-continue';
import * as apiClient from '../../lib/api-client';

// Mock the useParams hook
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ caseReference: 'CP-MOCK1' }),
    useNavigate: () => vi.fn(),
  };
});

describe('ContinueChannelPage', () => {
  const mockContinuity = {
    shared_field_names: ['Case reference', 'Issue summary', 'Status', 'Owner'],
    package_version: 4,
    generated_at: '2026-11-17T09:40:00Z',
  };

  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('renders loading state initially', () => {
    vi.spyOn(apiClient.apiClient, 'get').mockImplementation(() => new Promise(() => {}));
    
    render(
      <BrowserRouter>
        <ContinueChannelPage />
      </BrowserRouter>
    );
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('loads and displays continuity package', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockResolvedValue(mockContinuity);
    
    render(
      <BrowserRouter>
        <ContinueChannelPage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Get help')).toBeInTheDocument();
    });
    
    expect(screen.getByText(/Choose how you would like to carry on/)).toBeInTheDocument();
    expect(screen.getByText('Chat with an adviser')).toBeInTheDocument();
    expect(screen.getByText('Phone call')).toBeInTheDocument();
    expect(screen.getByText('Branch')).toBeInTheDocument();
  });

  it('displays shared fields panel', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockResolvedValue(mockContinuity);
    
    render(
      <BrowserRouter>
        <ContinueChannelPage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Get help')).toBeInTheDocument();
    });
    
    // Verify "What will be shared" accordion
    expect(screen.getByRole('button', { name: /what will be shared/i })).toBeInTheDocument();
    
    // Verify "What is never shared" section
    expect(screen.getByText('What is never shared')).toBeInTheDocument();
    expect(screen.getByText('Your full card number')).toBeInTheDocument();
    expect(screen.getByText('Passcodes and security answers')).toBeInTheDocument();
  });

  it('allows selecting a channel', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockResolvedValue(mockContinuity);
    
    render(
      <BrowserRouter>
        <ContinueChannelPage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Get help')).toBeInTheDocument();
    });
    
    // Find and click phone radio button
    const phoneRadio = screen.getByLabelText(/phone call/i, { selector: 'input' });
    fireEvent.click(phoneRadio);
    
    expect(phoneRadio).toBeChecked();
  });

  it('submits handoff when continue button is clicked', async () => {
    const mockPost = vi.spyOn(apiClient.apiClient, 'post').mockResolvedValue({});
    vi.spyOn(apiClient.apiClient, 'get').mockResolvedValue(mockContinuity);
    
    render(
      <BrowserRouter>
        <ContinueChannelPage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Get help')).toBeInTheDocument();
    });
    
    // Click submit button
    const submitButton = screen.getByRole('button', { name: /continue in chat/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith(
        '/cases/CP-MOCK1/handoffs',
        {
          to_channel: 'chat',
          from_channel: 'mobile_app',
          context_presented_flag: true,
        }
      );
    });
  });

  it('displays success message after handoff', async () => {
    vi.spyOn(apiClient.apiClient, 'post').mockResolvedValue({});
    vi.spyOn(apiClient.apiClient, 'get').mockResolvedValue(mockContinuity);
    
    render(
      <BrowserRouter>
        <ContinueChannelPage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Get help')).toBeInTheDocument();
    });
    
    // Click submit button
    const submitButton = screen.getByRole('button', { name: /continue in chat/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Your Case is ready in chat')).toBeInTheDocument();
      expect(screen.getByText(/Same Case: CP-MOCK1/)).toBeInTheDocument();
    });
  });

  it('displays error when loading fails', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockRejectedValue(new Error('Network error'));
    
    render(
      <BrowserRouter>
        <ContinueChannelPage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/Could not load continuity information/)).toBeInTheDocument();
    });
  });

  it('displays error when handoff fails', async () => {
    vi.spyOn(apiClient.apiClient, 'get').mockResolvedValue(mockContinuity);
    vi.spyOn(apiClient.apiClient, 'post').mockRejectedValue(new Error('Network error'));
    
    render(
      <BrowserRouter>
        <ContinueChannelPage />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.getByText('Get help')).toBeInTheDocument();
    });
    
    // Click submit button
    const submitButton = screen.getByRole('button', { name: /continue in chat/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Could not complete handoff/)).toBeInTheDocument();
    });
  });
});
