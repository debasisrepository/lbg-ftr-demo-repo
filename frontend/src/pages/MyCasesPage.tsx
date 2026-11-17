import { useEffect, useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { apiClient } from '../lib/api-client';
import { MyCasesList } from '../components/cases/MyCasesList';
import type { CaseListItem, CaseListResponse } from '../types/cases';

export function MyCasesPage() {
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCases = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get<CaseListResponse>('/v1/cases?limit=50&offset=0');
        setCases(response.items);
        setTotal(response.total);
      } catch (err) {
        console.error('Failed to fetch cases:', err);
        setError(err instanceof Error ? err.message : 'Failed to load cases');
      } finally {
        setLoading(false);
      }
    };

    fetchCases();
  }, []);

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h1 className="font-head text-3xl font-bold text-ink mb-s4">My Cases</h1>
        
        {loading && <p className="text-muted">Loading cases...</p>}
        {error && <p className="text-muted">{error}</p>}
        {!loading && !error && cases.length === 0 && <p className="text-muted">No cases found.</p>}
        {!loading && !error && cases.length > 0 && (
          <MyCasesList cases={cases} total={total} />
        )}
      </div>
    </Layout>
  );
}
