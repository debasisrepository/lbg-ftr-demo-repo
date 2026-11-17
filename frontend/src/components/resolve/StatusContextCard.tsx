interface StatusContextCardProps {
  title: string;
  message: string;
  lastUpdated: string;
  linkText?: string;
  onLinkClick?: () => void;
}

export function StatusContextCard({ title, message, lastUpdated, linkText, onLinkClick }: StatusContextCardProps) {
  return (
    <section className="flex gap-3 p-3 md:p-4 rounded-xl bg-[#E2EEF1] text-[#0E4A5C] border border-[#9CC3CF]" id="status-detail" role="status" aria-label="Service status that may be related to your problem">
      <svg className="w-5 h-5 flex-shrink-0 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M12 16v-4M12 8h.01" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      <div>
        <p className="text-[13px] font-bold uppercase tracking-wider">Service status</p>
        <p className="text-[15px]"><strong>{title}</strong> {message}</p>
        <p className="text-[13px] text-[#0E4A5C] mt-1">
          Last updated {lastUpdated}. We're showing this in case it's related. 
          {linkText && onLinkClick && (
            <> <a href="#status-detail" onClick={(e) => { e.preventDefault(); onLinkClick(); }} className="font-semibold underline">{linkText}</a></>
          )}
        </p>
      </div>
    </section>
  );
}
