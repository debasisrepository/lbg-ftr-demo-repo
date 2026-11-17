interface ProposalCardProps {
  title: string;
  description: string;
  scaNote: string;
  onConfirm: () => void;
  onDecline: () => void;
  disclaimer?: string;
}

export function ProposalCard({ title, description, scaNote, onConfirm, onDecline, disclaimer }: ProposalCardProps) {
  return (
    <section className="bg-white border-2 border-[#0B5D5B] rounded-xl p-4 flex flex-col gap-3" aria-labelledby="proposal-title">
      <h2 id="proposal-title" className="text-base font-bold flex items-center gap-2">
        <svg className="w-5 h-5 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
          <rect width="20" height="14" x="2" y="5" rx="2" strokeLinecap="round" strokeLinejoin="round"/>
          <line x1="2" x2="22" y1="10" y2="10" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        {title}
      </h2>
      <p className="text-[15px]">{description}</p>
      
      <div className="flex gap-3 p-3 rounded-lg bg-[#E2EEF1] text-[#0E4A5C] text-[14px]">
        <svg className="w-5 h-5 flex-shrink-0 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
          <rect width="18" height="11" x="3" y="11" rx="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M7 11V7a5 5 0 0 1 10 0v4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span><strong>{scaNote}</strong></span>
      </div>
      
      <div className="flex gap-2">
        <button 
          className="flex-1 min-h-[48px] px-4 rounded-full font-bold inline-flex items-center justify-center gap-2 bg-[#0B5D5B] text-white border-2 border-[#0B5D5B] focus-visible:outline focus-visible:outline-3 focus-visible:outline-[#1F6FEB] focus-visible:outline-offset-2"
          type="button"
          onClick={onConfirm}
        >
          Confirm and check it's me
        </button>
        <button 
          className="flex-1 min-h-[48px] px-4 rounded-full font-bold inline-flex items-center justify-center gap-2 bg-white text-[#0B5D5B] border-2 border-[#0B5D5B] focus-visible:outline focus-visible:outline-3 focus-visible:outline-[#1F6FEB] focus-visible:outline-offset-2"
          type="button"
          onClick={onDecline}
        >
          Not now
        </button>
      </div>
      
      {disclaimer && (
        <p className="flex gap-2 items-start text-[14px] text-[#4A5A60]">
          <svg className="w-4 h-4 flex-shrink-0 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M12 16v-4M12 8h.01" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span>{disclaimer}</span>
        </p>
      )}
    </section>
  );
}
