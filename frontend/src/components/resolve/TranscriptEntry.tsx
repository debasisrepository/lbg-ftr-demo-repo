interface TranscriptEntryProps {
  role: string;
  content: string;
  timestamp: string;
}

export function TranscriptEntry({ role, content, timestamp }: TranscriptEntryProps) {
  const isUser = role === 'customer';
  const isBot = role === 'assistant_ai';
  
  return (
    <div className={`flex flex-col gap-1 max-w-[92%] ${isUser ? 'self-end items-end' : ''}`}>
      <span className="text-[13px] font-bold text-[#4A5A60]">
        {isUser ? 'You' : isBot ? 'Assistant (AI)' : 'System'}
      </span>
      <div className={`p-3 md:p-4 rounded-2xl text-base ${
        isUser 
          ? 'bg-[#0B5D5B] text-white rounded-br-[4px]' 
          : 'bg-white border border-[#D5CFC0] rounded-bl-[4px]'
      }`}>
        {content}
      </div>
      <span className="text-[12px] text-[#4A5A60]">{timestamp}</span>
    </div>
  );
}
