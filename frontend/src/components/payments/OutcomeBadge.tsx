/**
 * OutcomeBadge component for Sent and Failed payment outcomes.
 * Shows icon + text with color-coding per wireframe_07.
 * Never uses color alone - always icon + text together for accessibility.
 */

interface OutcomeBadgeProps {
  status: 'Sent' | 'Failed';
}

export function OutcomeBadge({ status }: OutcomeBadgeProps) {
  if (status === 'Sent') {
    return (
      <span
        className="inline-flex items-center gap-2 self-start px-4 py-1.5 rounded-full font-bold text-lg text-[#1D6B37] bg-white border-2 border-white"
        role="status"
      >
        <svg
          className="w-6 h-6 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M7 12.5l3.5 3.5L17 9" />
        </svg>
        Sent
      </span>
    );
  }

  // Failed
  return (
    <span
      className="inline-flex items-center gap-2 self-start px-4 py-1.5 rounded-full font-bold text-lg text-[#BE222A] bg-white border-2 border-[#BE222A]"
      role="status"
    >
      <svg
        className="w-6 h-6 flex-shrink-0"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle cx="12" cy="12" r="10" />
        <path d="M8 8l8 8M16 8l-8 8" />
      </svg>
      Failed
    </span>
  );
}
