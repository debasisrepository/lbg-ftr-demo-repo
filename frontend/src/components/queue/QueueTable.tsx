import { formatCurrency } from '../../lib/format'
import type { QueueItem } from '../../types/queue'

interface QueueTableProps {
  items: QueueItem[]
  onOpenCustomer: (customerId: string) => void
}

export function QueueTable({ items, onOpenCustomer }: QueueTableProps) {
  const getStatePill = (item: QueueItem) => {
    if (item.is_non_standard) {
      const reason = item.non_standard_reason || 'flagged'
      return (
        <span>
          <span className="inline-block px-3 py-1 rounded-xl text-xs font-semibold border bg-[#FBEBDD] text-[#8A3A12] border-[#D9A27A]">
            Non-standard: {reason}
          </span>
          {item.non_standard_reason && (
            <span className="block text-xs text-[#8A3A12] mt-1">
              {getReasonText(item.non_standard_reason)}
            </span>
          )}
        </span>
      )
    }

    if (item.promise_indicator) {
      return (
        <span className="inline-block px-3 py-1 rounded-xl text-xs font-semibold border bg-[#E6EEF5] text-[#1F4468] border-[#9DB6CC]">
          Promise on file
        </span>
      )
    }

    return (
      <span className="inline-block px-3 py-1 rounded-xl text-xs font-semibold border bg-[#E3F1EC] text-[#0F5B46] border-[#7DB8A5]">
        Ready for action
      </span>
    )
  }

  const getReasonText = (reason: string): string => {
    const reasonMap: Record<string, string> = {
      disputed: 'Dispute open in SAP. Not worked as standard collections.',
      'unapplied cash': 'Unapplied payment received awaiting cash application.',
      'pending evidence': 'Proof of delivery requested; evidence-pending indicator set in SAP.',
    }
    return reasonMap[reason] || reason
  }

  return (
    <table className="w-full border-collapse">
      <caption className="text-left text-[#47525C] text-sm pb-2">
        Queue items ordered by rank
      </caption>
      <thead>
        <tr>
          <th className="text-left text-xs uppercase tracking-wider text-[#47525C] px-3 py-2 border-b-2 border-[#14283A]">
            Rank
          </th>
          <th className="text-left text-xs uppercase tracking-wider text-[#47525C] px-3 py-2 border-b-2 border-[#14283A]">
            Customer
          </th>
          <th className="text-right text-xs uppercase tracking-wider text-[#47525C] px-3 py-2 border-b-2 border-[#14283A]">
            Overdue ({items[0]?.currency_code || 'USD'})
          </th>
          <th className="text-right text-xs uppercase tracking-wider text-[#47525C] px-3 py-2 border-b-2 border-[#14283A]">
            Oldest (days)
          </th>
          <th className="text-left text-xs uppercase tracking-wider text-[#47525C] px-3 py-2 border-b-2 border-[#14283A]">
            Promise status
          </th>
          <th className="text-left text-xs uppercase tracking-wider text-[#47525C] px-3 py-2 border-b-2 border-[#14283A]">
            Queue state
          </th>
          <th className="text-left text-xs uppercase tracking-wider text-[#47525C] px-3 py-2 border-b-2 border-[#14283A]">
            Action
          </th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr
            key={item.queue_item_id}
            className={item.is_non_standard ? 'bg-[#FDF5EC]' : ''}
          >
            <td className="px-3 py-3 border-b border-[#E4DECF] font-bold text-[#14283A]">
              {item.priority_rank}
            </td>
            <td className="px-3 py-3 border-b border-[#E4DECF]">
              {item.customer_name}
              <br />
              <span className="text-[#47525C] text-xs">
                Cust. {item.customer_account_id.slice(0, 6)}
              </span>
            </td>
            <td className="px-3 py-3 border-b border-[#E4DECF] text-right">
              {formatCurrency(parseFloat(item.open_amount), item.currency_code)}
            </td>
            <td className="px-3 py-3 border-b border-[#E4DECF] text-right">
              {item.days_past_due}
            </td>
            <td className="px-3 py-3 border-b border-[#E4DECF]">
              {item.promise_indicator ? 'Promise on file' : 'None'}
            </td>
            <td className="px-3 py-3 border-b border-[#E4DECF]">{getStatePill(item)}</td>
            <td className="px-3 py-3 border-b border-[#E4DECF]">
              <button
                className="min-h-[36px] px-3 py-1 rounded border-2 border-[#14283A] bg-white text-[#14283A] font-bold text-sm"
                onClick={() => onOpenCustomer(item.customer_account_id)}
              >
                Open Customer 360
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
