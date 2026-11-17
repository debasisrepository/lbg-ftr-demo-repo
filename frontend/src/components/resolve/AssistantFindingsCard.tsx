interface Finding {
  label: string;
  value: string;
}

interface AssistantFindingsCardProps {
  findings: Finding[];
  note?: string;
}

export function AssistantFindingsCard({ findings, note }: AssistantFindingsCardProps) {
  return (
    <section className="bg-white border border-[#D5CFC0] rounded-xl p-4 flex flex-col gap-3" aria-labelledby="found-title">
      <h2 id="found-title" className="text-base font-bold flex items-center gap-2">
        <svg className="w-5 h-5 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="11" cy="11" r="8" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="m21 21-4.3-4.3" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        What I found
      </h2>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-[15px] m-0">
        {findings.map((finding, idx) => (
          <>
            <dt key={`label-${idx}`} className="text-[#4A5A60]">{finding.label}</dt>
            <dd key={`value-${idx}`} className="font-semibold m-0">{finding.value}</dd>
          </>
        ))}
      </dl>
      {note && <p className="text-[14px] text-[#4A5A60]">{note}</p>}
    </section>
  );
}
