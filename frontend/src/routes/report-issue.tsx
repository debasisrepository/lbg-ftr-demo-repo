import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button, Select, SelectItem, TextArea, InlineNotification } from '@carbon/react';
import { ChevronRight } from '@carbon/icons-react';
import { apiClient, ApiError } from '../lib/api-client';
import type { CaseCreateRequest, CaseCreateResponse } from '../types/api';

export function ReportIssuePage() {
  const navigate = useNavigate();
  const [issueType, setIssueType] = useState('card_declined');
  const [issueSummary, setIssueSummary] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CaseCreateResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setSubmitting(true);

    try {
      const request: CaseCreateRequest = {
        issue_type: issueType,
        issue_summary: issueSummary,
        origin_channel: 'mobile_app',
      };

      const response = await apiClient.post<CaseCreateResponse>('/cases', request);
      setResult(response);

      // Navigate based on outcome
      if (response.outcome === 'created' && response.case) {
        navigate(`/cases/${response.case.case_reference}`);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 flex flex-col gap-6">
      <Link to="/cases" className="inline-flex items-center gap-2 text-blue-600 hover:underline">
        ← My Cases
      </Link>

      <h1 className="cds--productive-heading-05">Report an issue</h1>

      <InlineNotification
        kind="info"
        lowContrast
        hideCloseButton
        subtitle="You are using our AI assistant to describe the issue. You can choose Talk to a person at any time."
      />

      <form onSubmit={handleSubmit} className="flex flex-col gap-6" aria-label="Report an issue">
        <Select
          id="issue-type"
          labelText="What is the issue about?"
          helperText="Choose the closest match. We will check whether we can track it as a Case."
          value={issueType}
          onChange={(e) => setIssueType(e.target.value)}
        >
          <SelectItem value="card_declined" text="Card payment declined" />
          <SelectItem value="payment_missing" text="Payment has not arrived" />
          <SelectItem value="signin_problem" text="Online banking sign-in problem" />
          <SelectItem value="general_query" text="Something else" />
        </Select>

        <TextArea
          id="issue-summary"
          labelText="Tell us what happened"
          helperText="Do not enter your full card number, passcode or security answers. 2000 characters at most."
          value={issueSummary}
          onChange={(e) => setIssueSummary(e.target.value)}
          rows={5}
          maxLength={2000}
        />

        {error && (
          <InlineNotification
            kind="error"
            title="Error"
            subtitle={error}
            lowContrast
          />
        )}

        <Button
          type="submit"
          kind="primary"
          disabled={submitting || !issueSummary.trim()}
          renderIcon={ChevronRight}
          className="self-start"
        >
          {submitting ? 'Sending...' : 'Send'}
        </Button>

        <Button
          kind="tertiary"
          as="a"
          href="#"
          className="self-start"
        >
          Talk to a person
        </Button>
      </form>

      {result && result.outcome === 'surfaced' && result.case && (
        <div className="mt-6 flex flex-col gap-4">
          <h2 className="cds--productive-heading-03">You already have an open Case for this</h2>
          <InlineNotification
            kind="info"
            lowContrast
            hideCloseButton
            title="We did not create a second Case"
            subtitle={`Your issue matches Case ${result.case.case_reference}, so you will not have to start again. You can keep using the same Case in any channel.`}
          />
          <div className="bg-gray-100 p-4">
            <p className="text-xs text-gray-600 mb-1">Case {result.case.case_reference}</p>
            <p className="cds--productive-heading-02 mb-2">{result.case.issue_title}</p>
            <p className="text-sm text-gray-600">
              Owner: {result.case.owner.owner_display_name} · Expected by {result.case.expected_by.customer_explanatory_text}
            </p>
          </div>
          <Link to={`/cases/${result.case.case_reference}`}>
            <Button kind="primary" renderIcon={ChevronRight}>
              Open Case {result.case.case_reference}
            </Button>
          </Link>
        </div>
      )}

      {result && result.outcome === 'not_eligible' && (
        <div className="mt-6 flex flex-col gap-4">
          <h2 className="cds--productive-heading-03">This one is handled in another part of the app</h2>
          <InlineNotification
            kind="warning"
            lowContrast
            hideCloseButton
            subtitle={result.redirect_message || 'We have not opened a Case for this. Use the existing journey in the app menu.'}
          />
          <Link to="/cases">
            <Button kind="tertiary" renderIcon={ChevronRight}>
              Go to the existing journey
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
