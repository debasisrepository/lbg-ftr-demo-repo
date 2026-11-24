import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueue } from '../hooks/useQueue'
import { QueueFilters, QueueFilterValues } from '../components/queue/QueueFilters'
import { QueueTable } from '../components/queue/QueueTable'
import { FreshnessNotice } from '../components/queue/FreshnessNotice'
import type { QueueGroup } from '../types/queue'

export function WorkQueuePage() {
  const navigate = useNavigate()
  const { data, isLoading, error, fetchQueue, triggerRefresh, checkRefreshStatus } = useQueue()
  const [activeTab, setActiveTab] = useState('active')
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [refreshMessage, setRefreshMessage] = useState('')

  useEffect(() => {
    fetchQueue({ queue_state: activeTab })
  }, [activeTab, fetchQueue])

  const handleFilterChange = (filters: QueueFilterValues) => {
    // Apply filters
    const params: Record<string, unknown> = { queue_state: activeTab }
    
    if (filters.showNonStandard === 'standard') {
      params.non_standard = false
    } else if (filters.showNonStandard === 'non-standard') {
      params.non_standard = true
    }

    if (filters.customerSearch) {
      // Note: The API spec doesn't have customer name filter, 
      // but we'll keep the UI for now
      // In a real implementation, this would need backend support
    }

    fetchQueue(params)
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    setRefreshMessage('Starting refresh...')
    try {
      const refreshResponse = await triggerRefresh({ scope: 'full' })
      const runId = refreshResponse.run_id

      // Poll for completion
      let completed = false
      let attempts = 0
      const maxAttempts = 30 // 30 seconds max

      while (!completed && attempts < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, 1000))
        const status = await checkRefreshStatus(runId)
        
        if (status.run_status === 'completed') {
          setRefreshMessage(`Refresh completed. ${status.items_ranked || 0} items ranked.`)
          completed = true
          // Refetch queue
          await fetchQueue({ queue_state: activeTab })
          setTimeout(() => setRefreshMessage(''), 3000)
        } else if (status.run_status === 'failed') {
          setRefreshMessage(`Refresh failed: ${status.error_summary || 'Unknown error'}`)
          completed = true
          setTimeout(() => setRefreshMessage(''), 5000)
        } else {
          setRefreshMessage('Refresh running...')
        }
        
        attempts++
      }

      if (!completed) {
        setRefreshMessage('Refresh is taking longer than expected. Please check back later.')
        setTimeout(() => setRefreshMessage(''), 5000)
      }
    } catch (err) {
      setRefreshMessage(
        err instanceof Error ? `Refresh failed: ${err.message}` : 'Refresh failed'
      )
      setTimeout(() => setRefreshMessage(''), 5000)
    } finally {
      setIsRefreshing(false)
    }
  }

  const handleOpenCustomer = (customerId: string) => {
    navigate(`/customer/${customerId}`)
  }

  const tabs: Array<{ key: string; label: string }> = [
    { key: 'active', label: 'Ready for action' },
    { key: 'promise_on_file', label: 'Promise on file' },
    { key: 'non_standard', label: 'Non-standard' },
  ]

  const getTabCount = (tabKey: string): number => {
    if (!data?.groups) return 0
    const group = data.groups.find((g: QueueGroup) => g.queue_state === tabKey)
    return group?.count || 0
  }

  return (
    <div>
      <div className="flex justify-between items-end mb-5">
        <div>
          <h1 className="text-[30px] leading-tight font-bold text-[#14283A] font-serif">
            Work queue
          </h1>
          <p className="text-[#56616B] mt-1">
            Overdue receivables grouped by actionable state and ordered by rank. Ranking factors:
            value, ageing, promise status, actionability.
          </p>
        </div>
        <button
          className="min-h-[44px] px-5 py-2 rounded border-2 border-[#14283A] bg-[#14283A] text-white font-bold disabled:opacity-50"
          onClick={handleRefresh}
          disabled={isRefreshing}
        >
          {isRefreshing ? 'Refreshing...' : 'Refresh queue'}
        </button>
      </div>

      {refreshMessage ? (
        <FreshnessNotice dataFreshness={new Date().toISOString()} message={refreshMessage} />
      ) : data?.data_freshness ? (
        <FreshnessNotice dataFreshness={data.data_freshness} />
      ) : null}

      <div className="flex gap-1 mb-0 border-b-2 border-[#14283A]" role="tablist" aria-label="Queue states">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            role="tab"
            aria-selected={activeTab === tab.key}
            className={`px-5 py-2 border border-b-0 rounded-t min-h-[44px] font-semibold ${
              activeTab === tab.key
                ? 'bg-[#14283A] text-white border-[#14283A]'
                : 'bg-[#EDE8DC] border-[#D5CDBB]'
            }`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
            <span
              className={`inline-block ml-2 px-2 rounded-full text-xs font-semibold ${
                activeTab === tab.key ? 'bg-white text-[#14283A]' : 'bg-white text-[#14283A]'
              }`}
            >
              {getTabCount(tab.key)}
            </span>
          </button>
        ))}
      </div>

      <section
        className="bg-white border border-[#D5CDBB] border-t-0 p-6 mb-6"
        aria-labelledby="queue-title"
      >
        <h2 id="queue-title" className="mb-3 text-xl font-bold text-[#14283A] font-serif">
          {activeTab === 'active' && 'Ready for action and flagged items'}
          {activeTab === 'promise_on_file' && 'Items with promise on file'}
          {activeTab === 'non_standard' && 'Non-standard items'}
        </h2>

        <QueueFilters onFilterChange={handleFilterChange} />

        {isLoading ? (
          <div className="text-center py-10 text-[#47525C]">Loading queue items...</div>
        ) : error ? (
          <div className="p-4 bg-[#FBEBDD] border border-[#D9A27A] rounded text-[#8A3A12]">
            Error loading queue: {error}
          </div>
        ) : data && data.items.length > 0 ? (
          <>
            <QueueTable items={data.items} onOpenCustomer={handleOpenCustomer} />
            <div className="flex justify-between items-center mt-4 text-[#47525C]">
              <span>
                Showing {data.offset + 1} to {Math.min(data.offset + data.limit, data.total)} of{' '}
                {data.total} items
              </span>
              <span>
                <button className="text-[#8A3A12] font-semibold underline" disabled>
                  Previous
                </button>
                {' | '}
                <button className="text-[#8A3A12] font-semibold underline" disabled>
                  Next
                </button>
              </span>
            </div>
          </>
        ) : (
          <div className="text-center py-10 text-[#47525C]">No items in this queue</div>
        )}
      </section>

      <div className="px-4 py-3 border border-dashed border-[#7A858F] rounded bg-[#FBF9F4] text-[#47525C] text-sm">
        <strong>Design note (FR-QUE-001).</strong> Disputed, unapplied and evidence-pending items
        are either removed from the standard queue or shown with the visible non-standard flag and
        reason, as shown by the shaded rows. Ordering uses a deterministic rank. An explanation
        view of ranking factors, exception taxonomy and aging indicators are deferred.
      </div>
    </div>
  )
}
