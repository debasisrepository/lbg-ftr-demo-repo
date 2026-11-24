import { formatDateTime } from '../../lib/format'

interface FreshnessNoticeProps {
  dataFreshness: string
  message?: string
}

export function FreshnessNotice({ dataFreshness, message }: FreshnessNoticeProps) {
  const defaultMessage = `Queue last refreshed ${formatDateTime(dataFreshness)} from SAP receivables data. Rank recalculates on every refresh when any factor changes.`
  
  return (
    <div
      role="status"
      className="flex gap-3 items-start px-4 py-3 border border-[#9DB6CC] bg-[#E6EEF5] text-[#14283A] rounded mb-5"
    >
      <span>{message || defaultMessage}</span>
    </div>
  )
}
