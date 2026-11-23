interface BadgeIconProps {
  variant: 'current' | 'stale' | 'unavailable';
  text: string;
}

export function BadgeIcon({ variant, text }: BadgeIconProps) {
  const styles = {
    current: {
      badge: 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-2xl text-sm font-bold border text-[#1D6B37] bg-white border-[#1D6B37]',
      icon: (
        <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="10" />
          <path d="M7 12.5l3.5 3.5L17 9" />
        </svg>
      ),
    },
    stale: {
      badge: 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-2xl text-sm font-bold border text-[#8A5A00] bg-[#FFF6E0] border-[#8A5A00]',
      icon: (
        <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 6v6l4 2" />
        </svg>
      ),
    },
    unavailable: {
      badge: 'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-2xl text-sm font-bold border text-[#BE222A] bg-white border-[#BE222A]',
      icon: (
        <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="10" />
          <path d="M5 5l14 14" />
        </svg>
      ),
    },
  };

  const style = styles[variant];

  return (
    <span className={style.badge}>
      {style.icon}
      {text}
    </span>
  );
}
