import { Time, Warning, Checkmark } from '@carbon/icons-react';
import type { CaseSummary } from '../../types/api';

interface StatusChipProps {
  case: CaseSummary;
}

export function StatusChip({ case: c }: StatusChipProps) {
  // Map lifecycle/status to icon and color
  let Icon = Time;
  let colorClass = 'text-blue-600';
  
  if (c.current_lifecycle_state === 'closed') {
    Icon = Checkmark;
    colorClass = 'text-green-600';
  } else if (c.status_code === 'action_required') {
    Icon = Warning;
    colorClass = 'text-yellow-600';
  }
  
  return (
    <div className="flex items-center gap-2 font-semibold mt-2">
      <Icon size={16} className={colorClass} />
      <span>{c.status_label}</span>
    </div>
  );
}
