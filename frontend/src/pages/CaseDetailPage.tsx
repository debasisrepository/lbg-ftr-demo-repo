import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Layout } from '../components/layout/Layout';
import { apiClient } from '../lib/api-client';
import type { CaseDetailResponse } from '../types/cases';

export function CaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const [caseDetail, setCaseDetail] = useState<CaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCase = async () => {
      if (!caseId) {
        setError('No case ID provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const detail = await apiClient.get<CaseDetailResponse>(`/v1/cases/${caseId}`);
        setCaseDetail(detail);
      } catch (err) {
        console.error('Failed to fetch case:', err);
        setError(err instanceof Error ? err.message : 'Failed to load case');
      } finally {
        setLoading(false);
      }
    };

    fetchCase();
  }, [caseId]);

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        {loading && <p className="text-muted">Loading case...</p>}
        {error && <p className="text-muted">{error}</p>}
        {!loading && !error && caseDetail && (
          <div>
            <h1 className="font-head text-3xl font-bold text-ink mb-s4">{caseDetail.case_ref}</h1>
            <div className="bg-surface border border-line rounded-xl p-s4">
              <dl className="grid grid-cols-[auto_1fr] gap-x-s3 gap-y-s2">
                <dt className="text-muted">Status:</dt>
                <dd className="m-0 font-semibold">{caseDetail.status}</dd>
                <dt className="text-muted">Classification:</dt>
                <dd className="m-0 font-semibold">{caseDetail.classification || 'N/A'}</dd>
                <dt className="text-muted">Owner:</dt>
                <dd className="m-0 font-semibold">{caseDetail.owner_colleague_display || caseDetail.owner_team_display || 'N/A'}</dd>
                <dt className="text-muted">Problem:</dt>
                <dd className="m-0">{caseDetail.problem_statement}</dd>
              </dl>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
