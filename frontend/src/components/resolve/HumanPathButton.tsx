interface HumanPathButtonProps {
  onClick: () => void;
  variant?: 'primary' | 'secondary';
}

export function HumanPathButton({ onClick, variant = 'secondary' }: HumanPathButtonProps) {
  const baseClasses = 'min-h-[48px] px-4 md:px-6 rounded-full font-bold inline-flex items-center justify-center gap-2 w-full cursor-pointer';
  const variantClasses = variant === 'primary' 
    ? 'bg-[#0B5D5B] text-white border-2 border-[#0B5D5B]'
    : 'bg-white text-[#0B5D5B] border-2 border-[#0B5D5B]';

  return (
    <button 
      className={`${baseClasses} ${variantClasses} focus-visible:outline focus-visible:outline-3 focus-visible:outline-[#1F6FEB] focus-visible:outline-offset-2`}
      type="button"
      onClick={onClick}
    >
      <svg className="w-5 h-5 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      Talk to a person
    </button>
  );
}
