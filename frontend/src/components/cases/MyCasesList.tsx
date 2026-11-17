import { CaseRow } from './CaseRow';
import type { CaseListItem } from '../../types/cases';

interface MyCasesListProps {
  cases: CaseListItem[];
  total: number;
  highlightCaseId?: string;
}

export function MyCasesList({ cases, total, highlightCaseId }: MyCasesListProps) {
  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return `Today, ${date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`;
    } else if (date.toDateString() === yesterday.toDateString()) {
      return `Yesterday, ${date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`;
    } else {
      return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
    }
  };

  return (
    <section aria-labelledby="mycases-title" className="flex flex-col gap-s3">
      <div className="list-title flex justify-between items-baseline">
        <h2 id="mycases-title" className="text-lg font-head">Now in My Cases</h2>
        <span className="text-sm text-muted">{total} open</span>
      </div>
      
      {cases.map((caseItem) => (
        <CaseRow
          key={caseItem.id}
          name={caseItem.classification || 'Case'}
          caseRef={caseItem.case_ref}
          status={caseItem.status === 'new' ? 'With our team' : caseItem.status}
          statusColor={caseItem.status === 'waiting_for_customer' ? 'warn' : 'info'}
          owner={caseItem.owner_colleague_display || caseItem.owner_team_display || 'Support team'}
          lastUpdate={formatDate(caseItem.last_update_at)}
          expectedBy={caseItem.expected_by_at ? formatDate(caseItem.expected_by_at) : 'When you reply'}
          isNew={caseItem.id === highlightCaseId}
          isActive={caseItem.id === highlightCaseId}
        />
      ))}
    </section>
  );
}
