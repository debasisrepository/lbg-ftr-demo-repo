import type { TranscriptEntryResponse } from '../../types/colleague';

interface TranscriptPanelProps {
  entries: TranscriptEntryResponse[];
  total: number;
}

export function TranscriptPanel({ entries, total }: TranscriptPanelProps) {
  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
  };

  const getRoleAvatar = (role: string) => {
    if (role === 'customer') return { class: 'av-c bg-[#DCE7F5] text-[#17325C]', initials: 'SO' };
    if (role === 'assistant') return { class: 'av-a bg-primary-soft text-[#083F3D]', initials: 'AI' };
    if (role === 'system') return { class: 'av-s bg-[#E8E6DF] text-[#2F3B3F]', initials: 'SY' };
    return { class: 'av-h bg-[#F7E3C9] text-[#5A3300]', initials: 'PN' };
  };

  const getRoleLabel = (role: string) => {
    if (role === 'customer') return 'Sam Okafor';
    if (role === 'assistant') return 'Assistant (AI)';
    if (role === 'system') return 'System';
    return 'Colleague';
  };

  return (
    <section className="panel bg-surface border border-line rounded-xl p-s4 flex flex-col gap-s3" aria-labelledby="tr-title">
      <h2 id="tr-title" className="text-[15px] font-bold flex items-center gap-s2">
        <svg className="icon w-[18px] h-[18px]" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m22 2-7 20-4-9-9-4Z"/>
          <path d="M22 2 11 13"/>
        </svg>
        Conversation so far
        <span className="count ml-auto text-[13px] font-semibold text-muted">Same thread the customer sees · {total} messages</span>
      </h2>
      <div className="thread flex flex-col gap-s3" role="log" aria-label="Transcript">
        {entries.map((entry) => {
          const avatar = getRoleAvatar(entry.role);
          const isSystem = entry.role === 'system';
          const isNote = entry.visibility_scope === 'colleague_only';

          return (
            <div key={entry.entry_id} className={`entry ${isSystem ? 'sys' : ''} ${isNote ? 'note' : ''} flex gap-s3`}>
              <span className={`av ${avatar.class} w-8 h-8 rounded-2xl inline-flex items-center justify-center text-xs font-bold flex-shrink-0`} aria-hidden="true">
                {avatar.initials}
              </span>
              <div className="body flex-1 flex flex-col gap-0.5">
                <span className="meta text-[13px] text-muted flex gap-s2 items-center flex-wrap">
                  <strong className="text-ink">{getRoleLabel(entry.role)}</strong> · {formatTime(entry.occurred_at)}
                  {entry.visibility_scope === 'colleague_only' && ' · Colleague-only note'}
                </span>
                <p className={`bubble p-s3 rounded-xl ${isSystem ? 'bg-transparent border-0 p-0 italic text-muted' : isNote ? 'bg-warn-bg border border-[#E6C766] text-warn-ink' : 'bg-[#F7F6F1] border border-line'}`}>
                  {entry.content_text}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
