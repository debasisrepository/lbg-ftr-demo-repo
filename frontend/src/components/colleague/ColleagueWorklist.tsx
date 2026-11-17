interface WorklistItem {
  caseRef: string;
  title: string;
  detail: string;
  isActive?: boolean;
}

interface ColleagueWorklistProps {
  items: WorklistItem[];
  total: number;
}

export function ColleagueWorklist({ items, total }: ColleagueWorklistProps) {
  return (
    <section className="panel bg-surface border border-line rounded-xl p-s4 flex flex-col gap-s3" aria-labelledby="wl-title" id="worklist">
      <h2 id="wl-title" className="text-[15px] font-bold flex items-center gap-s2">
        My team's cases
        <span className="count ml-auto text-[13px] font-semibold text-muted">{total} open</span>
      </h2>
      <ul className="worklist list-none p-0 flex flex-col gap-s2">
        {items.map((item, index) => (
          <li
            key={index}
            className={`${item.isActive ? 'active border-2 border-primary bg-primary-soft' : 'border border-line'} rounded-lg p-s2 px-s3 text-sm flex flex-col gap-0.5`}
          >
            <strong>{item.caseRef} · {item.title}</strong>
            <span className="small text-[13px] text-muted">{item.detail}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
