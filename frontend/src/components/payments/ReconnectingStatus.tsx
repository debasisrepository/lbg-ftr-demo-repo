/**
 * ReconnectingStatus component shown while loading payment details
 * after session timeout using idempotency key to reconnect.
 */

export function ReconnectingStatus() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F7F9F8]">
      <div className="text-center px-6">
        <div className="inline-flex items-center justify-center w-12 h-12 mb-4 rounded-full bg-[#0074CD]">
          <svg
            className="w-6 h-6 text-white animate-spin"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
        <p className="text-lg font-bold text-[#002563]">Reconnecting...</p>
        <p className="text-sm text-[#4F5155] mt-2">
          Loading your payment details
        </p>
      </div>
    </div>
  );
}
