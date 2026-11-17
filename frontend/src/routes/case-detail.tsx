import { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button, Tile, InlineNotification } from '@carbon/react';
import { ArrowLeft, ChevronRight } from '@carbon/icons-react';
import { apiClient } from '../lib/api-client';
import { CaseDetail } from '../types/api';
import { useState } from 'react';
import { StatusChip } from '../components/case/StatusChip';
import { OwnerBlock } from '../components/case/OwnerBlock';
import { ExpectedByBlock } from '../components/case/ExpectedByBlock';
import { formatDateTime } from '../lib/utils';

/**
 * Case Detail page - wireframe_03_case_detail
 * Route: /cases/:caseReference
 * Features: FR-002, FR-003, FR-004, FR-008, FR-009, FR-017, FR-019, FR-029
 */
export function CaseDetailPage() {
  const { caseReference } = useParams<{ caseReference: string }>();
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!caseReference) return;

    async function fetchCase() {
      setLoading(true);
      setError(null);
      try {
        const data = await apiClient.get<CaseDetail>(`/cases/${caseReference}`);
        setCaseData(data);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Failed to load case details');
        }
      } finally {
        setLoading(false);
      }
    }

    fetchCase();
  }, [caseReference]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <p>Loading case details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <InlineNotification
          kind="error"
          title="Error"
          subtitle={error}
          lowContrast
        />
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <p>Case not found</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 flex flex-col gap-6">
      <Link to="/cases" className="inline-flex items-center gap-2 no-underline">
        <ArrowLeft size={16} />
        My Cases
      </Link>

      <header className="flex flex-col gap-3">
        <p className="text-xs text-gray-600">
          Case {caseData.case_reference} · opened {formatDateTime(caseData.opened_at)}
        </p>
        <h1 className="cds--productive-heading-05">{caseData.issue_title}</h1>
        <StatusChip case={caseData} />
        <p>{caseData.status_summary_text}</p>
      </header>

      {caseData.outage_impact_banner_text && (
        <div className="flex flex-col gap-2">
          <InlineNotification
            kind="warning"
            title="An outage may slow this Case down"
            subtitle={caseData.outage_impact_banner_text}
            lowContrast
          />
          <Link to="/status" className="text-sm underline">
            View Service status
          </Link>
        </div>
      )}

      <section aria-labelledby="who-h" className="flex flex-col gap-4">
        <h2 className="cds--productive-heading-03" id="who-h">Who has it and when</h2>
        
        <dl className="grid grid-cols-1 gap-4">
          <Tile className="flex flex-col gap-2">
            <dt className="text-xs text-gray-600">Owner</dt>
            <dd className="cds--productive-heading-02">{caseData.owner.owner_display_name}</dd>
            <dd className="text-xs text-gray-600">
              Accountable for resolving this Case. Since {formatDateTime(caseData.owner.effective_from)}.
            </dd>
          </Tile>

          <Tile className="flex flex-col gap-2">
            <dt className="text-xs text-gray-600">Expected by</dt>
            {caseData.expected_by.expected_by_at ? (
              <>
                <dd className="cds--productive-heading-02">
                  {formatDateTime(caseData.expected_by.expected_by_at)}
                </dd>
                <dd className="text-xs text-gray-600">
                  {caseData.expected_by.customer_explanatory_text}
                </dd>
              </>
            ) : (
              <>
                <dd className="cds--productive-heading-02">Timing is under review</dd>
                <dd className="text-xs text-gray-600">
                  {caseData.expected_by.customer_explanatory_text}
                </dd>
              </>
            )}
          </Tile>

          {caseData.latest_meaningful_update_text && (
            <Tile className="flex flex-col gap-2">
              <dt className="text-xs text-gray-600">
                Latest update
                {caseData.latest_meaningful_update_at && 
                  ` · ${formatDateTime(caseData.latest_meaningful_update_at)}`}
              </dt>
              <dd>{caseData.latest_meaningful_update_text}</dd>
            </Tile>
          )}

          {caseData.next_step_text && (
            <Tile className="flex flex-col gap-2">
              <dt className="text-xs text-gray-600">What happens next</dt>
              <dd>{caseData.next_step_text}</dd>
            </Tile>
          )}
        </dl>
      </section>

      <section aria-labelledby="more-h" className="flex flex-col gap-3">
        <h2 className="cds--productive-heading-03" id="more-h">More about this Case</h2>
        
        <Link 
          to={`/cases/${caseData.case_reference}/history`}
          className="flex justify-between items-center min-h-12 px-4 border-b border-gray-300 no-underline bg-gray-100"
        >
          <span>See every update</span>
          <ChevronRight size={16} />
        </Link>

        <Link 
          to={`/cases/${caseData.case_reference}/continue`}
          className="flex justify-between items-center min-h-12 px-4 border-b border-gray-300 no-underline bg-gray-100"
        >
          <span>Continue in chat, by phone or in branch</span>
          <ChevronRight size={16} />
        </Link>
      </section>

      <Button 
        kind="tertiary" 
        className="w-full"
        onClick={() => {
          // This would navigate to continue page
          window.location.href = `/cases/${caseData.case_reference}/continue`;
        }}
      >
        Talk to a person
      </Button>

      {caseData.closed_at && caseData.outcome_summary && (
        <Tile className="flex flex-col gap-2">
          <dt className="text-xs text-gray-600">Outcome</dt>
          <dd>{caseData.outcome_summary}</dd>
          <dd className="text-xs text-gray-600">Closed {formatDateTime(caseData.closed_at)}</dd>
        </Tile>
      )}
    </div>
  );
}
