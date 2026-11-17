interface ChecklistCardProps {
  items: {
    icon: 'check' | 'paperclip' | 'msg';
    label: string;
  }[];
}

export function ChecklistCard({ items }: ChecklistCardProps) {
  const icons = {
    check: (
      <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="m9 12 2 2 4-4"/>
      </svg>
    ),
    paperclip: (
      <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
      </svg>
    ),
    msg: (
      <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
  };

  return (
    <section className="card bg-surface border border-line rounded-xl p-s4 flex flex-col gap-s3" aria-labelledby="kept-title">
      <h2 id="kept-title" className="text-base font-bold">What we've already sent to the team</h2>
      <ul className="kept list-none p-0 flex flex-col gap-s2">
        {items.map((item, index) => (
          <li key={index} className="flex gap-s2 text-[15px] items-start">
            <span className="text-ok-ink mt-0.5">{icons[item.icon]}</span>
            <span>{item.label}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
