import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Toggle } from '@carbon/react';
import { ChevronRight } from '@carbon/icons-react';
import { useCases, useStatus, useNotifications } from '../hooks/use-resource';
import { StatusChip } from '../components/case/StatusChip';
import { OwnerBlock } from '../components/case/OwnerBlock';
import { ExpectedByBlock } from '../components/case/ExpectedByBlock';
import { StatusBanner } from '../components/status/StatusBanner';
import { NotificationList } from '../components/communication/NotificationList';
import { formatDateTime } from '../lib/utils';

export function CaseListPage() {
  const [includeClosed, setIncludeClosed] = useState(true);
  const { data: casesData, loading: casesLoading, error: casesError } = useCases(includeClosed);
  const { data: status } = useStatus();
  const { data: notificationsData } = useNotifications();

  const cases = casesData?.items || [];
  const notifications = notificationsData?.items || [];

  return (
    <div className="max-w-4xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="cds--productive-heading-05">My Cases</h1>

      {status && <StatusBanner status={status} />}

      <Link to="/report">
        <Button kind="primary" renderIcon={ChevronRight} className="w-full justify-between">
          Report a new issue
        </Button>
      </Link>

      <section className="flex flex-col gap-4" aria-labelledby="cases-h">
        <div className="flex justify-between items-center">
          <h2 className="cds--productive-heading-03" id="cases-h">Your Cases</h2>
          <div className="flex items-center gap-3">
            <span id="closed-label" className="text-sm">Show closed Cases</span>
            <Toggle
              id="show-closed-toggle"
              labelA=""
              labelB=""
              labelText=""
              hideLabel
              toggled={includeClosed}
              onToggle={(checked) => setIncludeClosed(checked)}
              aria-labelledby="closed-label"
              size="sm"
            />
          </div>
        </div>

        {casesLoading && <p>Loading cases...</p>}
        {casesError && <p className="text-red-600">{casesError}</p>}

        {!casesLoading && cases.length === 0 && (
          <p className="text-gray-600">No cases to display.</p>
        )}

        {cases.length > 0 && (
          <>
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
            <p className="text-xs text-gray-600">Showing {cases.length} of {cases.length} Cases</p>
          </>
        )}
      </section>

      <NotificationList notifications={notifications} />
    </div>
  );
}
