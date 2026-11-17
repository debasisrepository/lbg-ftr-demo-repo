import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ReportIssuePage } from '../report-issue';
import { apiClient, ApiError } from '../../lib/api-client';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

beforeEach(() => {
  vi.clearAllMocks();
});

describe('ReportIssuePage', () => {
  it('renders Report an issue heading', () => {
    render(
      <BrowserRouter>
        <ReportIssuePage />
      </BrowserRouter>
    );

    expect(screen.getByText('Report an issue')).toBeInTheDocument();
  });

  it('renders form fields', () => {
    render(
      <BrowserRouter>
        <ReportIssuePage />
      </BrowserRouter>
    );

    expect(screen.getByLabelText('What is the issue about?')).toBeInTheDocument();
    expect(screen.getByLabelText('Tell us what happened')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Send/i })).toBeInTheDocument();
  });

  it('submits form and navigates on created outcome', async () => {
    const postSpy = vi.spyOn(apiClient, 'post');
    const mockResponse = {
      outcome: 'created',
      case: {
        case_reference: 'CP-99999',
        customer_party_id: 'CUST-001',
        brand: 'lloyds',
        issue_type: 'card_declined',
        classification_source: 'eligibility_rule',
        issue_title: 'Card Declined',
        issue_summary: 'My card was declined',
        origin_channel: 'mobile_app',
        current_lifecycle_state: 'case_created',
        status_code: 'received',
        status_label: 'Received',
        status_summary_text: 'Your case has been received',
        latest_meaningful_update_text: 'Case received',
        latest_meaningful_update_at: null,
        next_step_text: null,
        outage_impact_banner_text: null,
        owner: {
          owner_team_code: 'INTAKE_DEFAULT',
          owner_semantic_label: 'Intake Team',
          owner_display_name: 'Intake & Triage',
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
        continuity_state: 'current',
      },
    };

    postSpy.mockResolvedValue(mockResponse);

    render(
      <BrowserRouter>
        <ReportIssuePage />
      </BrowserRouter>
    );

    const textarea = screen.getByLabelText('Tell us what happened');
    fireEvent.change(textarea, { target: { value: 'My card was declined at the store' } });

    const submitButton = screen.getByRole('button', { name: /Send/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/cases/CP-99999');
    });
  });

  it('displays surfaced outcome with existing case', async () => {
    const postSpy = vi.spyOn(apiClient, 'post');
    const mockResponse = {
      outcome: 'surfaced',
      case: {
        case_reference: 'CP-12345',
        customer_party_id: 'CUST-001',
        brand: 'lloyds',
        issue_type: 'card_declined',
        classification_source: 'eligibility_rule',
        issue_title: 'Card Declined',
        issue_summary: 'Previous issue',
        origin_channel: 'mobile_app',
        current_lifecycle_state: 'case_created',
        status_code: 'received',
        status_label: 'Received',
        status_summary_text: 'Your case has been received',
        latest_meaningful_update_text: 'Case received',
        latest_meaningful_update_at: null,
        next_step_text: null,
        outage_impact_banner_text: null,
        owner: {
          owner_team_code: 'INTAKE_DEFAULT',
          owner_semantic_label: 'Intake Team',
          owner_display_name: 'Intake & Triage',
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
        continuity_state: 'current',
      },
    };

    postSpy.mockResolvedValue(mockResponse);

    render(
      <BrowserRouter>
        <ReportIssuePage />
      </BrowserRouter>
    );

    const textarea = screen.getByLabelText('Tell us what happened');
    fireEvent.change(textarea, { target: { value: 'Same issue again' } });

    const submitButton = screen.getByRole('button', { name: /Send/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('You already have an open Case for this')).toBeInTheDocument();
    });

    expect(screen.getAllByText(/Case CP-12345/).length).toBeGreaterThan(0);
  });

  it('displays not_eligible outcome', async () => {
    const postSpy = vi.spyOn(apiClient, 'post');
    const mockResponse = {
      outcome: 'not_eligible',
      redirect_message: 'Use the existing support journey',
    };

    postSpy.mockResolvedValue(mockResponse);

    render(
      <BrowserRouter>
        <ReportIssuePage />
      </BrowserRouter>
    );

    const textarea = screen.getByLabelText('Tell us what happened');
    fireEvent.change(textarea, { target: { value: 'General question' } });

    const submitButton = screen.getByRole('button', { name: /Send/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('This one is handled in another part of the app')).toBeInTheDocument();
    });
  });

  it('displays error on API failure', async () => {
    const postSpy = vi.spyOn(apiClient, 'post');
    postSpy.mockRejectedValue(
      new ApiError(422, 'Restricted data detected')
    );

    render(
      <BrowserRouter>
        <ReportIssuePage />
      </BrowserRouter>
    );

    const textarea = screen.getByLabelText('Tell us what happened');
    fireEvent.change(textarea, { target: { value: 'My card number is 1234567890123456' } });

    const submitButton = screen.getByRole('button', { name: /Send/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Restricted data detected/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
