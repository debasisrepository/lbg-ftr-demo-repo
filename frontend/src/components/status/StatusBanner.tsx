import { InlineNotification } from '@carbon/react';
import type { StatusSnapshot } from '../../types/api';

interface StatusBannerProps {
  status: StatusSnapshot;
}

export function StatusBanner({ status }: StatusBannerProps) {
  if (status.status_state !== 'disruption' || status.incidents.length === 0) {
    return null;
  }

  const firstIncident = status.incidents[0];

  return (
    <InlineNotification
      kind="warning"
      lowContrast
      hideCloseButton
      title={firstIncident.customer_impact_summary}
      subtitle={`We are working on it. Last updated ${new Date(status.generated_at).toLocaleTimeString()}.`}
    />
  );
}
