interface CaseRowProps {
  name: string;
  caseRef: string;
  status: string;
  statusColor: 'info' | 'warn';
  owner: string;
  lastUpdate: string;
  expectedBy: string;
  isNew?: boolean;
  isActive?: boolean;
}

export function CaseRow({ name, caseRef, status, statusColor, owner, lastUpdate, expectedBy, isNew, isActive }: CaseRowProps) {
  const baseClasses = "case-row bg-surface rounded-xl p-s4 flex flex-col gap-s2";
  const borderClasses = isActive ? "border-2 border-primary" : "border border-line";
  
  const statusIcons = {
    info: (
      <svg className="icon-sm w-4 h-4" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
    warn: (
      <svg className="icon-sm w-4 h-4" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12 6 12 12 16 14"/>
      </svg>
    ),
  };

  return (
    <article className={`${baseClasses} ${borderClasses}`} aria-label={`Case ${caseRef}, ${name}`}>
      <div className="top flex justify-between gap-s2 items-start">
        <div>
          <p className="name font-bold">{name}</p>
          <p className="ref text-[13px] text-muted">
            Case {caseRef}
            {isNew && <> · <span className="new text-xs font-bold bg-ok-bg text-ok-ink py-0.5 px-s2 rounded-[10px]">New</span></>}
          </p>
        </div>
        <span className={`state inline-flex items-center gap-s1 text-sm font-bold py-0.5 px-s3 rounded-xl whitespace-nowrap ${statusColor === 'info' ? 'bg-info-bg text-info-ink' : 'bg-warn-bg text-warn-ink'}`}>
          {statusIcons[statusColor]}
          {status}
        </span>
      </div>
      <dl className="grid grid-cols-[auto_1fr] gap-x-s3 gap-y-s1 text-sm">
        <dt className="text-muted">Owner</dt>
        <dd className="m-0 font-semibold">{owner}</dd>
        <dt className="text-muted">Last update</dt>
        <dd className="m-0 font-semibold">{lastUpdate}</dd>
        <dt className="text-muted">Expected by</dt>
        <dd className="m-0 font-semibold">{expectedBy}</dd>
      </dl>
    </article>
  );
}
