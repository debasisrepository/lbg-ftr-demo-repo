import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ResolvePage } from '../pages/ResolvePage';
import * as apiClient from '../lib/api-client';

// Mock the api client
vi.mock('../lib/api-client', () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

// Mock react-router-dom navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('ResolvePage', () => {
  const renderResolvePage = () => {
    return render(
      <BrowserRouter>
        <ResolvePage />
      </BrowserRouter>
    );
  };

  it('should render intake screen with all key elements', () => {
    renderResolvePage();
    
    // Check AI disclosure
    expect(screen.getByText(/You're talking to an AI assistant/i)).toBeInTheDocument();
    
    // Check page title
    expect(screen.getByRole('heading', { name: /What's gone wrong/i })).toBeInTheDocument();
    
    // Check transaction picker
    expect(screen.getByText(/Or start from something you can see/i)).toBeInTheDocument();
    
    // Check textarea
    expect(screen.getByLabelText(/Describe the problem/i)).toBeInTheDocument();
    
    // Check submit button
    expect(screen.getByRole('button', { name: /Send to the assistant/i })).toBeInTheDocument();
    
    // Check human path button
    expect(screen.getByRole('button', { name: /Talk to a person/i })).toBeInTheDocument();
  });

  it('should allow typing in the problem description', () => {
    renderResolvePage();
    
    const textarea = screen.getByLabelText(/Describe the problem/i) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'New problem description' } });
    
    expect(textarea.value).toBe('New problem description');
  });

  it('should update character count', () => {
    renderResolvePage();
    
    const textarea = screen.getByLabelText(/Describe the problem/i);
    fireEvent.change(textarea, { target: { value: 'Test' } });
    
    expect(screen.getByText(/4 of 4,000/i)).toBeInTheDocument();
  });

  it('should allow selecting transactions', () => {
    renderResolvePage();
    
    const radios = screen.getAllByRole('radio');
    expect(radios.length).toBeGreaterThan(0);
    
    // First radio should be checked by default
    expect(radios[0]).toBeChecked();
    
    // Click second radio
    fireEvent.click(radios[1]);
    expect(radios[1]).toBeChecked();
    expect(radios[0]).not.toBeChecked();
  });

  it('should submit resolve request and navigate to session', async () => {
    const mockResponse = {
      session_id: 'test-session-123',
      thread_id: 'test-thread-456',
      state: 'active',
      human_path_shown: true,
      new_entries: [],
    };

    vi.mocked(apiClient.apiClient.post).mockResolvedValueOnce(mockResponse);

    renderResolvePage();
    
    const textarea = screen.getByLabelText(/Describe the problem/i);
    fireEvent.change(textarea, { target: { value: 'Test problem' } });
    
    const submitButton = screen.getByRole('button', { name: /Send to the assistant/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(apiClient.apiClient.post).toHaveBeenCalledWith(
        '/v1/resolve',
        expect.objectContaining({
          message_text: 'Test problem',
        })
      );
    });
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/resolve/test-session-123');
    });
  });

  it('should disable submit button when text is empty', () => {
    renderResolvePage();
    
    const textarea = screen.getByLabelText(/Describe the problem/i);
    fireEvent.change(textarea, { target: { value: '' } });
    
    const submitButton = screen.getByRole('button', { name: /Send to the assistant/i });
    expect(submitButton).toBeDisabled();
  });

  it('should show error message on API failure', async () => {
    vi.mocked(apiClient.apiClient.post).mockRejectedValueOnce(
      new Error('Network error')
    );

    renderResolvePage();
    
    const textarea = screen.getByLabelText(/Describe the problem/i);
    fireEvent.change(textarea, { target: { value: 'Test problem' } });
    
    const submitButton = screen.getByRole('button', { name: /Send to the assistant/i });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });
  });

  it('should display service status context card', () => {
    renderResolvePage();
    
    expect(screen.getByText(/We have a problem with payments right now/i)).toBeInTheDocument();
    expect(screen.getByText(/Service status/i)).toBeInTheDocument();
  });

  it('should show what happens next section', () => {
    renderResolvePage();
    
    expect(screen.getByText(/What happens when you send this/i)).toBeInTheDocument();
    expect(screen.getByText(/We check what we can see on your account/i)).toBeInTheDocument();
  });
});
