interface CapabilityBannerProps {
  variant: 'partial' | 'unavailable' | 'stale';
  message: string;
}

export function CapabilityBanner({ variant, message }: CapabilityBannerProps) {
  const isError = variant === 'unavailable';
  
  return (
    <div
      className={`flex gap-3 p-4 rounded-lg ${
        isError
          ? 'border-2 border-[#BE222A] bg-white'
          : 'border-l-4 border-[#8A5A00] bg-[#FFF6E0]'
      }`}
      role="status"
    >
      <svg
        className={`w-5 h-5 flex-shrink-0 ${isError ? 'text-[#BE222A]' : 'text-[#8A5A00]'}`}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path d="M12 3l10 18H2z" />
        <path d="M12 10v5M12 18v.5" />
      </svg>
      <div className="flex-1">
        <div dangerouslySetInnerHTML={{ __html: message }} />
      </div>
    </div>
  );
}
