interface EvidenceItem {
  name: string;
  detail: string;
  status: 'checked' | 'waiting';
}

interface EvidencePanelProps {
  items: EvidenceItem[];
  onRequestEvidence: (label: string, why: string) => Promise<void>;
}

export function EvidencePanel({ items, onRequestEvidence }: EvidencePanelProps) {
  return (
    <section className="panel bg-surface border border-line rounded-xl p-s4 flex flex-col gap-s3" aria-labelledby="evi-title">
      <h2 id="evi-title" className="text-[15px] font-bold flex items-center gap-s2">
        <svg className="icon w-[18px] h-[18px]" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
          <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
        </svg>
        Evidence
        <span className="count ml-auto text-[13px] font-semibold text-muted">{items.filter(i => i.status === 'checked').length} received · {items.filter(i => i.status === 'waiting').length} requested</span>
      </h2>
      
      {items.map((item, index) => (
        <div key={index} className="ev flex items-center gap-s3 p-s3 border border-line rounded-lg">
          <svg className="icon w-[18px] h-[18px]" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
            <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
          </svg>
          <span className="main flex-1 flex flex-col">
            <span className="name font-semibold text-sm break-all">{item.name}</span>
            <span className="small text-[13px] text-muted">{item.detail}</span>
          </span>
          <span className={`badge inline-flex items-center gap-s1 text-[13px] font-bold py-0.5 px-s3 rounded-xl whitespace-nowrap ${item.status === 'checked' ? 'bg-ok-bg text-ok-ink' : 'bg-warn-bg text-warn-ink'}`}>
            {item.status === 'checked' ? (
              <>
                <svg className="icon-sm w-3.5 h-3.5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="m9 12 2 2 4-4"/>
                </svg>
                Checked
              </>
            ) : (
              <>
                <svg className="icon-sm w-3.5 h-3.5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
                Waiting
              </>
            )}
          </span>
        </div>
      ))}
      
      <form className="compose flex flex-col gap-s2 border-t border-line pt-s3" onSubmit={(e) => e.preventDefault()} aria-label="Ask the customer for more evidence">
        <label htmlFor="evi-label" className="font-bold text-sm">Ask for more evidence in this case</label>
        <input id="evi-label" type="text" defaultValue="A photo of the receipt, if you have one" className="min-h-10 px-s3 font-[inherit] border-2 border-[#5C6B70] rounded-lg bg-surface text-ink" />
        <label htmlFor="evi-why" className="small text-[13px]">Why we need it (the customer reads this)</label>
        <input id="evi-why" type="text" defaultValue="It helps us check whether you made this purchase." className="min-h-10 px-s3 font-[inherit] border-2 border-[#5C6B70] rounded-lg bg-surface text-ink" />
        <button className="btn btn-secondary min-h-10 px-s4 rounded-[20px] font-bold inline-flex items-center justify-center gap-s2 cursor-pointer bg-surface text-primary border-2 border-primary" type="button">
          Send evidence request
        </button>
      </form>
    </section>
  );
}
