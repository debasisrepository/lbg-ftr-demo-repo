import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, TextInput } from '@carbon/react';
import { ChevronRight } from '@carbon/icons-react';
import { apiClient } from '../lib/api-client';
import { CaseSummary } from '../types/api';
import { StatusChip } from '../components/case/StatusChip';
import { OwnerBlock } from '../components/case/OwnerBlock';
import { ExpectedByBlock } from '../components/case/ExpectedByBlock';
import { formatDateTime } from '../lib/utils';

/**
 * Colleague case retrieval page
 * Allows colleagues to look up cases by customer party ID
 */
export function ColleagueCaseRetrievalPage() {
  const [partyId, setPartyId] = useState('');
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!partyId.trim()) {
      setError('Please enter a customer party ID');
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(false);

    try {
      const response = await apiClient.get<{ items: CaseSummary[] }>(`/colleague/cases?party_id=${encodeURIComponent(partyId)}`);
      setCases(response.items || []);
      setSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve cases');
      setCases([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="cds--productive-heading-05">Retrieve Customer Cases</h1>

      <div className="flex gap-4 items-end">
        <TextInput
          id="party-id-input"
          labelText="Customer Party ID"
          placeholder="Enter party ID"
          value={partyId}
          onChange={(e) => setPartyId(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleSearch();
            }
          }}
          className="flex-1"
        />
        <Button onClick={handleSearch} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </Button>
      </div>

      {error && <p className="text-red-600">{error}</p>}

      {searched && !loading && cases.length === 0 && (
        <p className="text-gray-600">No cases found for this customer.</p>
      )}

      {cases.length > 0 && (
        <section className="flex flex-col gap-4">
          <h2 className="cds--productive-heading-03">Cases for Party ID: {partyId}</h2>
          <ul className="flex flex-col gap-4 list-none p-0">
            {cases.map((c) => (
              <li key={c.case_reference}>
                <Link
                  to={`/cases/${c.case_reference}`}
                  className="block bg-gray-100 p-4 hover:bg-gray-200 transition-colors no-underline text-inherit"
                  aria-label={`Case ${c.case_reference}, ${c.issue_title}, status ${c.status_label}, owner ${c.owner.owner_display_name}`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <p className="text-xs text-gray-600 mb-1">
                        Case {c.case_reference} · opened {formatDateTime(c.opened_at)}
                      </p>
                      <p className="cds--productive-heading-02">{c.issue_title}</p>
                    </div>
                    <ChevronRight size={16} className="text-gray-600 flex-shrink-0 ml-2" />
                  </div>
                  
                  <StatusChip case={c} />
                  
                  <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 mt-3 text-sm">
                    <OwnerBlock owner={c.owner} />
                    <ExpectedByBlock expectedBy={c.expected_by} />
                    <dt className="text-gray-600">Latest update</dt>
                    <dd>
                      {c.latest_meaningful_update_at 
                        ? formatDateTime(c.latest_meaningful_update_at)
                        : 'No updates yet'}
                    </dd>
                  </dl>
                </Link>
              </li>
            ))}
          </ul>
          <p className="text-xs text-gray-600">Showing {cases.length} case(s)</p>
        </section>
      )}
    </div>
  );
}
