import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Tile, InlineNotification } from '@carbon/react';
import { ChevronRight, Checkmark, WarningAlt, Time } from '@carbon/icons-react';
import { apiClient } from '../lib/api-client';
import { StatusSnapshot } from '../types/api';
import { IncidentCard } from '../components/status/IncidentCard';
import { formatDateTime } from '../lib/utils';

/**
 * Service Status page - wireframe_07_service_status
 * Route: /status (public, no RequireAuth)
 * Features: FR-019, FR-021
 */
export function ServiceStatusPage() {
  const [status, setStatus] = useState<StatusSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const data = await apiClient.get<StatusSnapshot>('/status');
      setStatus(data);
      setError(null);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to load service status');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();

    // Poll every max_age_seconds
    const interval = setInterval(() => {
      if (status?.max_age_seconds) {
        fetchStatus();
      }
    }, (status?.max_age_seconds || 60) * 1000);

    return () => clearInterval(interval);
  }, [status?.max_age_seconds]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <p>Loading service status...</p>
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

  if (!status) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <p>Service status unavailable</p>
      </div>
    );
  }

  const hasDisruption = status.status_state === 'disruption';
  const activeIncidents = status.incidents.filter(i => i.incident_state !== 'resolved');
  const resolvedIncidents = status.incidents.filter(i => i.incident_state === 'resolved');

  return (
    <div className="max-w-4xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="cds--productive-heading-05">Service status</h1>

      {hasDisruption && (
        <section aria-labelledby="now-h" className="flex flex-col gap-4">
          <h2 className="cds--productive-heading-03" id="now-h">Happening now</h2>
          
          {activeIncidents.map((incident) => (
            <IncidentCard key={incident.incident_reference} incident={incident} />
          ))}
        </section>
      )}

      {!hasDisruption && (
        <InlineNotification
          kind="success"
          title="Everything is working"
          subtitle={`We are not aware of any problems right now. Last checked ${formatDateTime(status.generated_at)}.`}
          lowContrast
        />
      )}

      {resolvedIncidents.length > 0 && (
        <section aria-labelledby="resolved-h" className="flex flex-col gap-4">
          <h2 className="cds--productive-heading-03" id="resolved-h">Recently resolved</h2>
          
          {resolvedIncidents.map((incident) => (
            <IncidentCard key={incident.incident_reference} incident={incident} />
          ))}
        </section>
      )}

      {hasDisruption && status.lifeline_available && (
        <Button 
          kind="primary" 
          renderIcon={ChevronRight}
          className="w-full justify-between"
          as={Link}
          to="/lifeline"
        >
          See what you can do now
        </Button>
      )}

      <p className="text-xs text-gray-600">
        Last updated {formatDateTime(status.generated_at)}
      </p>
    </div>
  );
}
