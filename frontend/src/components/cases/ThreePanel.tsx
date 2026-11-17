interface ThreePanelProps {
  owner: {
    team: string;
    note: string;
  };
  nextUpdate: {
    time: string;
    note: string;
  };
  whatWeKnow: {
    summary: string;
    detail: string;
  };
}

export function ThreePanel({ owner, nextUpdate, whatWeKnow }: ThreePanelProps) {
  return (
    <section className="card bg-surface border border-line rounded-xl p-s4 flex flex-col gap-s3" aria-labelledby="three-title">
      <h2 id="three-title" className="text-base font-bold">What you need to know</h2>
      <div className="three flex flex-col gap-s4">
        <div className="row flex gap-s3">
          <span className="ico w-10 h-10 rounded-full bg-primary-soft text-primary flex items-center justify-center flex-shrink-0">
            <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </span>
          <div>
            <p className="k text-[13px] font-bold text-muted uppercase tracking-wide">Who has it</p>
            <p className="v text-base font-semibold">{owner.team}</p>
            <p className="sub text-sm text-muted">{owner.note}</p>
          </div>
        </div>
        <div className="row flex gap-s3">
          <span className="ico w-10 h-10 rounded-full bg-primary-soft text-primary flex items-center justify-center flex-shrink-0">
            <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect width="18" height="18" x="3" y="4" rx="2"/>
              <path d="M16 2v4"/>
              <path d="M8 2v4"/>
              <path d="M3 10h18"/>
            </svg>
          </span>
          <div>
            <p className="k text-[13px] font-bold text-muted uppercase tracking-wide">Next update expected by</p>
            <p className="v text-base font-semibold">{nextUpdate.time}</p>
            <p className="sub text-sm text-muted">{nextUpdate.note}</p>
          </div>
        </div>
        <div className="row flex gap-s3">
          <span className="ico w-10 h-10 rounded-full bg-primary-soft text-primary flex items-center justify-center flex-shrink-0">
            <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </span>
          <div>
            <p className="k text-[13px] font-bold text-muted uppercase tracking-wide">What we know</p>
            <p className="v text-base font-semibold">{whatWeKnow.summary}</p>
            <p className="sub text-sm text-muted">{whatWeKnow.detail}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
