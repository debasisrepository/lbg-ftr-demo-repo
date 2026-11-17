interface AiDisclosureProps {
  variant?: 'notice' | 'inline';
}

export function AiDisclosure({ variant = 'notice' }: AiDisclosureProps) {
  if (variant === 'inline') {
    return (
      <div className="flex gap-3 p-3 rounded-xl bg-[#E0EFEE] text-[#083F3D] border border-[#8FC2BF]">
        <svg className="w-5 h-5 flex-shrink-0 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 8V4H8" strokeLinecap="round" strokeLinejoin="round"/>
          <rect width="16" height="12" x="4" y="8" rx="2"/>
          <path d="M2 14h2M20 14h2M15 13v2M9 13v2" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <p className="text-[15px]">You're talking to an AI assistant. You can talk to a person at any time.</p>
      </div>
    );
  }

  return (
    <section className="flex gap-3 p-3 md:p-4 rounded-xl bg-[#E0EFEE] text-[#083F3D] border border-[#8FC2BF]" aria-label="You are talking to an AI assistant">
      <svg className="w-5 h-5 flex-shrink-0 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 8V4H8" strokeLinecap="round" strokeLinejoin="round"/>
        <rect width="16" height="12" x="4" y="8" rx="2"/>
        <path d="M2 14h2M20 14h2M15 13v2M9 13v2" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      <div>
        <p className="text-[13px] font-bold uppercase tracking-wider">AI assistant</p>
        <p className="text-[15px]">You're talking to an AI assistant, not a person. You can talk to a person at any time.</p>
      </div>
    </section>
  );
}
