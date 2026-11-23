export function PendingBadge() {
  return (
    <span
      className="inline-flex items-center gap-2 self-start px-4 py-1.5 rounded-full font-bold text-lg text-[#8A5A00] bg-[#FFF6E0] border-2 border-[#8A5A00]"
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
        <path d="M12 6v6l4 2" />
      </svg>
      Pending
    </span>
  );
}
