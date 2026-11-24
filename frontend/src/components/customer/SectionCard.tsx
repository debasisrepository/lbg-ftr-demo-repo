import { ReactNode } from 'react'
import { SectionStatus } from '../../types/customer'

interface SectionCardProps {
  title: string
  status: SectionStatus
  reason?: string
  children: ReactNode
  'aria-labelledby'?: string
}

export function SectionCard({ title, status, reason, children, 'aria-labelledby': ariaLabelledby }: SectionCardProps) {
  const titleId = ariaLabelledby || `section-${title.toLowerCase().replace(/\s+/g, '-')}`
  
  const statusPillClasses = {
    available: 'bg-[#E3F1EC] text-[#0F5B46] border-[#7DB8A5]',
    unavailable: 'bg-[#FBEBDD] text-[#8A3A12] border-[#D9A27A]',
    masked: 'bg-[#E6EEF5] text-[#1F4468] border-[#9DB6CC]',
  }

  return (
    <section className="bg-white border border-[#D5CDBB] rounded-md p-5 mb-6" aria-labelledby={titleId}>
      <div className="flex justify-between items-baseline mb-3">
        <h2 id={titleId} className="text-lg font-bold text-[#14283A] font-serif m-0">
          {title}
        </h2>
        <span
          className={`inline-block py-0.5 px-2.5 rounded-xl text-xs font-semibold border ${statusPillClasses[status]}`}
        >
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </span>
      </div>
      {status === 'unavailable' && reason ? (
        <div className="p-4 border-2 border-dashed border-[#A4481A] bg-[#FDF5EC] rounded" role="status">
          <strong className="text-[#8A3A12]">Section unavailable.</strong> {reason}
        </div>
      ) : (
        children
      )}
    </section>
  )
}
