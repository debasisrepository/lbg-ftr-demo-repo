import { Link } from 'react-router-dom';
import { ChevronRight } from '@carbon/icons-react';
import { useNotifications } from '../hooks/use-resource';
import { formatDateTime } from '../lib/utils';

/**
 * Notifications list page
 */
export function NotificationsPage() {
  const { data: notificationsData, loading, error } = useNotifications();

  const notifications = notificationsData?.items || [];

  return (
    <div className="max-w-4xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="cds--productive-heading-05">Notifications</h1>

      {loading && <p>Loading notifications...</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && notifications.length === 0 && (
        <p className="text-gray-600">No notifications to display.</p>
      )}

      {notifications.length > 0 && (
        <ul className="flex flex-col gap-4 list-none p-0">
          {notifications.map((notification) => (
            <li key={notification.id}>
              <Link
                to={notification.deep_link_target}
                className="block bg-gray-100 p-4 hover:bg-gray-200 transition-colors no-underline text-inherit"
                aria-label={`Notification ${notification.notification_type}, ${notification.safe_preview_text}`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <p className="text-xs text-gray-600 mb-1">
                      {notification.notification_type} · {formatDateTime(notification.created_at)}
                    </p>
                    <p className="cds--productive-heading-02">{notification.safe_preview_text}</p>
                    {notification.case_reference && (
                      <p className="text-sm text-gray-600 mt-1">Case {notification.case_reference}</p>
                    )}
                  </div>
                  <ChevronRight size={16} className="text-gray-600 flex-shrink-0 ml-2" />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
