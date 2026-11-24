import { useState } from 'react'

export interface QueueFilterValues {
  showNonStandard: 'all' | 'standard' | 'non-standard'
  customerSearch: string
}

interface QueueFiltersProps {
  onFilterChange: (filters: QueueFilterValues) => void
}

export function QueueFilters({ onFilterChange }: QueueFiltersProps) {
  const [showNonStandard, setShowNonStandard] = useState<'all' | 'standard' | 'non-standard'>('all')
  const [customerSearch, setCustomerSearch] = useState('')

  const handleShowChange = (value: 'all' | 'standard' | 'non-standard') => {
    setShowNonStandard(value)
    onFilterChange({ showNonStandard: value, customerSearch })
  }

  const handleSearchChange = (value: string) => {
    setCustomerSearch(value)
    onFilterChange({ showNonStandard, customerSearch: value })
  }

  return (
    <div className="flex gap-4 items-center mb-4">
      <div className="flex items-center gap-2">
        <label htmlFor="flag-filter" className="font-semibold">
          Show
        </label>
        <select
          id="flag-filter"
          name="flag-filter"
          className="min-h-[40px] px-3 py-2 border border-[#7A858F] rounded bg-white min-w-[200px]"
          value={showNonStandard}
          onChange={(e) => handleShowChange(e.target.value as 'all' | 'standard' | 'non-standard')}
        >
          <option value="all">Standard and non-standard (flagged)</option>
          <option value="standard">Standard only</option>
          <option value="non-standard">Non-standard only</option>
        </select>
      </div>
      <div className="flex items-center gap-2">
        <label htmlFor="cust-search" className="font-semibold">
          Customer
        </label>
        <input
          id="cust-search"
          name="cust-search"
          type="text"
          className="min-h-[40px] px-3 py-2 border border-[#7A858F] rounded bg-white min-w-[200px]"
          value={customerSearch}
          onChange={(e) => handleSearchChange(e.target.value)}
          placeholder="Search by customer name or number"
          aria-label="Search by customer name or number"
          title="Search by customer name or number"
        />
      </div>
    </div>
  )
}
