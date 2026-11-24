import { useLanding } from '../hooks/useLanding'
import { useAuth } from '../lib/use-auth'
import { RoleSwitcher } from '../components/workspace/RoleSwitcher'
import { formatCurrency, formatDateTime } from '../lib/format'
import { Link } from 'react-router-dom'

export function LandingPage() {
  const { user } = useAuth()
  const { data, isLoading, error, switchRole } = useLanding()

  const handleRoleChange = async (roleCode: string) => {
    try {
      await switchRole(roleCode)
    } catch (err) {
      console.error('Failed to switch role:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-[#47525C]">Loading workspace...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-[#FBEBDD] border border-[#D9A27A] rounded text-[#8A3A12]">
        Error loading landing: {error}
      </div>
    )
  }

  if (!data) {
    return null
  }

  const queueWidget = data.widgets.find((w) => w.widget_code === 'queue_summary')
  const promisesWidget = data.widgets.find((w) => w.widget_code === 'open_promises')

  const queueData = queueWidget?.widget_data as {
    groups?: Array<{ queue_state: string; count: number; total_amount: number }>
    top_items?: Array<{
      customer_name: string
      open_amount: number
      currency_code: string
      days_past_due: number
      queue_state: string
    }>
  }

  const promisesData = promisesWidget?.widget_data as {
    items?: Array<{
      customer_name: string
      promised_amount: number
      currency_code: string
      promised_date: string
      scope_description: string
    }>
  }

  const greeting = user?.display_name ? `Good morning, ${user.display_name.split(' ')[0]}` : 'Good morning'
  const lastRefresh = formatDateTime(data.data_freshness).split(', ')[1] || '07:42 UTC'

  return (
    <div>
      <div className="flex justify-between items-end mb-6">
        <div>
          <h1 className="text-[30px] leading-tight font-bold text-[#14283A] font-serif">
            {greeting}
          </h1>
          <p className="text-[#56616B] mt-1">
            Home view for the {data.active_role_label} role profile. Last queue refresh {lastRefresh}.
          </p>
        </div>
        <RoleSwitcher
          activeRoleCode={data.active_role_code}
          activeRoleLabel={data.active_role_label}
          availableRoles={data.available_roles}
          onRoleChange={handleRoleChange}
        />
      </div>

      {data.available_roles.length > 1 && (
        <div
          role="note"
          className="flex gap-3 items-start px-4 py-3 border border-[#9DB6CC] bg-[#E6EEF5] text-[#14283A] rounded mb-6"
        >
          <strong>Two roles assigned to you:</strong>
          <span>
            {data.active_role_label} (active) and {data.available_roles.filter(r => r.role_code !== data.active_role_code)[0]?.role_label}. Selecting another role reloads this page with only the widgets and queues that role is authorized to see.
          </span>
        </div>
      )}

      <div className="flex gap-6">
        <div className="flex-[2]">
          {queueWidget && (
            <section
              className="bg-white border border-[#D5CDBB] rounded-md p-6 mb-6"
              aria-labelledby="queue-panel-title"
            >
              <div className="flex justify-between items-baseline mb-4">
                <h2 id="queue-panel-title" className="text-xl font-bold text-[#14283A] font-serif">
                  My work queue
                </h2>
                <Link to="/queue" className="text-[#8A3A12] font-semibold underline">
                  Open full work queue
                </Link>
              </div>

              {queueData?.groups && (
                <div className="flex gap-4 mb-5">
                  {queueData.groups.slice(0, 3).map((group, idx) => (
                    <div
                      key={group.queue_state}
                      className={`flex-1 px-4 py-3 border border-[#D5CDBB] rounded bg-[#FBF9F4] ${
                        idx === 2 ? 'border-l-4 border-l-[#A4481A]' : ''
                      }`}
                    >
                      <div className="text-[30px] leading-tight font-bold text-[#14283A] font-serif">
                        {group.count}
                      </div>
                      <div className="text-sm text-[#47525C]">
                        {group.queue_state === 'active' ? 'Ready for collections action' : 
                         group.queue_state === 'promise_on_file' ? 'Promise on file' : 
                         'Non-standard (flagged with reason)'}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {queueData?.top_items && queueData.top_items.length > 0 && (
                <table className="w-full border-collapse">
                  <caption className="text-left text-[#47525C] text-sm pb-2">
                    Top 3 items by current rank
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
                        Overdue ({queueData.top_items[0]?.currency_code || 'USD'})
                      </th>
                      <th className="text-right text-xs uppercase tracking-wider text-[#47525C] px-3 py-2 border-b-2 border-[#14283A]">
                        Oldest (days)
                      </th>
                      <th className="text-left text-xs uppercase tracking-wider text-[#47525C] px-3 py-2 border-b-2 border-[#14283A]">
                        State
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {queueData.top_items.slice(0, 3).map((item, idx) => (
                      <tr key={idx}>
                        <td className="px-3 py-3 border-b border-[#E4DECF]">{idx + 1}</td>
                        <td className="px-3 py-3 border-b border-[#E4DECF]">
                          {item.customer_name}
                        </td>
                        <td className="px-3 py-3 border-b border-[#E4DECF] text-right">
                          {formatCurrency(item.open_amount, item.currency_code)}
                        </td>
                        <td className="px-3 py-3 border-b border-[#E4DECF] text-right">
                          {item.days_past_due}
                        </td>
                        <td className="px-3 py-3 border-b border-[#E4DECF]">
                          <span className={`inline-block px-3 py-1 rounded-xl text-xs font-semibold border ${
                            item.queue_state === 'active' 
                              ? 'bg-[#E3F1EC] text-[#0F5B46] border-[#7DB8A5]'
                              : 'bg-[#E6EEF5] text-[#1F4468] border-[#9DB6CC]'
                          }`}>
                            {item.queue_state === 'active' ? 'Ready for action' : 'Promise on file'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          )}
        </div>

        <div className="flex-1">
          {promisesWidget && (
            <section
              className="bg-white border border-[#D5CDBB] rounded-md p-6 mb-6"
              aria-labelledby="promise-panel-title"
            >
              <div className="flex justify-between items-baseline mb-4">
                <h2 id="promise-panel-title" className="text-xl font-bold text-[#14283A] font-serif">
                  Open promises to pay
                </h2>
                <Link to="/promise/new" className="text-[#8A3A12] font-semibold underline">
                  View all
                </Link>
              </div>

              {promisesData?.items && promisesData.items.length > 0 ? (
                <>
                  <ul className="list-none m-0 p-0">
                    {promisesData.items.slice(0, 3).map((item, idx) => (
                      <li
                        key={idx}
                        className={`py-3 ${
                          idx < (promisesData.items?.length || 0) - 1 ? 'border-b border-[#E4DECF]' : ''
                        }`}
                      >
                        <div className="font-bold">{item.customer_name}</div>
                        <div className="text-[#47525C] text-sm">
                          {formatCurrency(item.promised_amount, item.currency_code)} promised for{' '}
                          {new Date(item.promised_date).toLocaleDateString('en-US', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric',
                          })}{' '}
                          · {item.scope_description}
                        </div>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-4">
                    <Link
                      to="/promise/new"
                      className="inline-block min-h-[44px] px-5 py-2 rounded border-2 border-[#14283A] bg-white text-[#14283A] font-bold"
                    >
                      Record a promise to pay
                    </Link>
                  </div>
                </>
              ) : (
                <p className="text-[#47525C]">No open promises</p>
              )}
            </section>
          )}

          <div className="mt-8 px-4 py-3 border border-dashed border-[#7A858F] rounded bg-[#FBF9F4] text-[#47525C] text-sm">
            <strong>Design note (FR-CAPA-001).</strong> The server builds this page from the role
            profile. Widgets that the active role is not entitled to are not rendered at all, not
            merely disabled. Deferred widgets (personalized summary, saved filters, KPIs) are not
            shown in the MVP.
          </div>
        </div>
      </div>
    </div>
  )
}
