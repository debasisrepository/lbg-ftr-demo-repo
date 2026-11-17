interface CaseHeroProps {
  title: string;
  message: string;
}

export function CaseHero({ title, message }: CaseHeroProps) {
  return (
    <section className="hero bg-primary text-primary-ink rounded-2xl p-s5 flex flex-col gap-s3" aria-labelledby="hero-title">
      <span className="tick flex items-center gap-s2 font-bold text-sm uppercase tracking-wider">
        <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <path d="m9 12 2 2 4-4"/>
        </svg>
        Case opened
      </span>
      <h1 id="hero-title" className="font-head text-[28px] leading-tight">{title}</h1>
      <p className="text-base">{message}</p>
    </section>
  );
}
