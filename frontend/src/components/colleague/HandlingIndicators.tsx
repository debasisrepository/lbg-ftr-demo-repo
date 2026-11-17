interface IndicatorProps {
  type: 'risk' | 'warn';
  title: string;
  description: string;
}

function Indicator({ type, title, description }: IndicatorProps) {
  const className = type === 'risk' ? 'alert bg-risk-bg text-risk-ink' : 'alert bg-warn-bg text-warn-ink';
  const icon = type === 'risk' ? (
    <svg className="icon w-[18px] h-[18px]" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 16 14"/>
    </svg>
  ) : (
    <svg className="icon w-[18px] h-[18px]" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
    </svg>
  );

  return (
    <div className={`${className} flex gap-s3 p-s3 rounded-lg text-sm`}>
      {icon}
      <div>
        <strong className="block">{title}</strong>
        {description}
      </div>
    </div>
  );
}

interface HandlingIndicatorsProps {
  indicators: IndicatorProps[];
}

export function HandlingIndicators({ indicators }: HandlingIndicatorsProps) {
  return (
    <section className="panel bg-surface border border-line rounded-xl p-s4 flex flex-col gap-s3" aria-labelledby="ind-title">
      <h2 id="ind-title" className="text-[15px] font-bold flex items-center gap-s2">Handling indicators</h2>
      {indicators.map((indicator, index) => (
        <Indicator key={index} {...indicator} />
      ))}
      <p className="small text-[13px] text-muted">Indicators are for colleagues only. They are never shown to the customer.</p>
    </section>
  );
}
