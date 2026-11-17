import { Tile, Tag } from '@carbon/react';
import { WarningAlt, Time, Checkmark } from '@carbon/icons-react';
import { StatusIncident } from '../../types/api';
import { formatDateTime } from '../../lib/utils';

interface IncidentCardProps {
  incident: StatusIncident;
}

/**
 * Incident card component for service status display
 */
export function IncidentCard({ incident }: IncidentCardProps) {
  const isResolved = incident.incident_state === 'resolved';
  const isMonitoring = incident.incident_state === 'monitoring';
  
  // Determine icon and color based on state
  const getStatusIcon = () => {
    if (isResolved) {
      return <Checkmark size={16} className="text-green-600" />;
    }
    if (isMonitoring) {
      return <Time size={16} className="text-blue-600" />;
    }
    return <WarningAlt size={16} className="text-yellow-600" />;
  };

  const getStatusColor = () => {
    if (isResolved) return 'green';
    if (isMonitoring) return 'blue';
    return 'warm-gray';
  };

  // Get the latest publication
  const latestPublication = incident.publications.length > 0 
    ? incident.publications[incident.publications.length - 1]
    : null;

  return (
    <Tile className="flex flex-col gap-3">
      <div className="flex items-start gap-2">
        {getStatusIcon()}
        <div className="flex-1">
          <p className="cds--productive-heading-02">
            {latestPublication?.headline_text || incident.customer_impact_summary}
          </p>
          {isResolved && (
            <Tag type={getStatusColor()} size="sm" className="mt-2">
              Resolved
            </Tag>
          )}
          {isMonitoring && (
            <Tag type={getStatusColor()} size="sm" className="mt-2">
              Monitoring
            </Tag>
          )}
        </div>
      </div>

      {latestPublication && (
        <p>{latestPublication.summary_text}</p>
      )}

      {latestPublication && latestPublication.affected_journeys.length > 0 && (
        <p className="text-xs text-gray-600">
          Affected: {latestPublication.affected_journeys.join(', ')}
        </p>
      )}

      <p className="text-xs text-gray-600">
        Started {formatDateTime(incident.started_at)}
        {latestPublication && ` · Updated ${formatDateTime(latestPublication.published_at)}`}
        {incident.resolved_at && ` · Resolved ${formatDateTime(incident.resolved_at)}`}
      </p>
    </Tile>
  );
}
