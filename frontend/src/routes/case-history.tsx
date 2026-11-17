import { useParams, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Button, InlineNotification, SkeletonText } from '@carbon/react';
import { ArrowLeft, Checkmark, Information, Time } from '@carbon/icons-react';
import { apiClient } from '../lib/api-client';
import { HistoryEvent, Page } from '../types/api';
import { formatDateTime } from '../lib/utils';
import './case-history.css';

/**
 * Case History page - wireframe_04
 * Displays chronological history of case events with pagination
 * Features FR-032, FR-004, FR-008, FR-009
 */
export function CaseHistoryPage() {
  const { caseReference } = useParams<{ caseReference: string }>();
  const [events, setEvents] = useState<HistoryEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadHistory() {
      if (!caseReference) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const response = await apiClient.get<Page<HistoryEvent>>(
          `/cases/${caseReference}/history?limit=${limit}&offset=${offset}`
        );
        
        // API returns { items, total, limit, offset }
        setEvents(response.items);
        setTotal(response.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load history');
      } finally {
        setLoading(false);
      }
    }
    
    loadHistory();
  }, [caseReference, limit, offset]);

  const handleLoadMore = () => {
    setOffset(offset + limit);
  };

  const hasMore = offset + events.length < total;

  // Map event types to icons
  const getEventIcon = (eventType: string) => {
    if (eventType === 'CaseCaptured') {
      return <Checkmark size={20} />;
    }
    if (eventType === 'OwnerChanged' || eventType === 'ExpectedByChanged') {
      return <Information size={20} />;
    }
    if (eventType === 'CaseStatusChanged') {
      return <Time size={20} />;
    }
    if (eventType === 'ChannelHandoffRecorded') {
      return <Information size={20} />;
    }
    if (eventType === 'ProtectedActionRequested' || eventType === 'ProtectedActionOutcome') {
      return <Information size={20} />;
    }
    return <Information size={20} />;
  };

  // Check if an event is superseded (for OwnerChanged and ExpectedByChanged)
  const isSuperseded = (event: HistoryEvent, index: number): boolean => {
    // An event is superseded if there's a later event of the same type
    const laterEvents = events.slice(0, index);
    return laterEvents.some(e => e.event_type === event.event_type);
  };

  if (loading && events.length === 0) {
    return (
      <div className="case-history-page">
        <Link to={`/cases/${caseReference}`} className="back-link">
          <ArrowLeft size={16} />
          Case {caseReference}
        </Link>
        
        <header className="history-header">
          <p className="case-meta">
            Case {caseReference}
          </p>
          <h1 className="cds--productive-heading-05">Case history</h1>
          <p>Every update in the order it happened. Nothing is overwritten. Newest first.</p>
        </header>

        <div className="history-skeleton">
          <SkeletonText />
          <SkeletonText />
          <SkeletonText />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="case-history-page">
        <Link to={`/cases/${caseReference}`} className="back-link">
          <ArrowLeft size={16} />
          Case {caseReference}
        </Link>
        
        <InlineNotification
          kind="error"
          title="Failed to load history"
          subtitle={error}
          lowContrast
        />
      </div>
    );
  }

  return (
    <div className="case-history-page">
      <Link to={`/cases/${caseReference}`} className="back-link">
        <ArrowLeft size={16} />
        Case {caseReference}
      </Link>
      
      <header className="history-header">
        <p className="case-meta">
          Case {caseReference}
        </p>
        <h1 className="cds--productive-heading-05">Case history</h1>
        <p>Every update in the order it happened. Nothing is overwritten. Newest first.</p>
      </header>

      {events.length === 0 ? (
        <p className="cds--body-01">No history events found.</p>
      ) : (
        <>
          <ol className="history-timeline" aria-label="Case history, newest first">
            {events.map((event, index) => {
              const superseded = isSuperseded(event, index);
              
              return (
                <li key={event.id} className="timeline-step">
                  <span className="step-icon">
                    {getEventIcon(event.event_type)}
                  </span>
                  <div className="step-content">
                    <p className="cds--productive-heading-01">
                      {event.summary_text}
                      {superseded && (
                        <span className="superseded-badge">Earlier</span>
                      )}
                    </p>
                    <p className="cds--label-01 event-meta">
                      {formatDateTime(event.event_timestamp)}
                    </p>
                  </div>
                </li>
              );
            })}
          </ol>

          <p className="history-count cds--label-01">
            Showing {events.length} of {total} updates
          </p>

          {hasMore && (
            <Button
              kind="tertiary"
              onClick={handleLoadMore}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Load more'}
            </Button>
          )}

          <Button
            kind="tertiary"
            as={Link}
            to={`/cases/${caseReference}`}
            className="back-button"
          >
            Back to Case
          </Button>
        </>
      )}
    </div>
  );
}
