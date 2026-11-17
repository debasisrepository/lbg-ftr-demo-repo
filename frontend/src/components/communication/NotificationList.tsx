import type { NotificationItem } from '../../types/api';
import { formatDateTime } from '../../lib/utils';

interface NotificationListProps {
  notifications: NotificationItem[];
}

export function NotificationList({ notifications }: NotificationListProps) {
  if (notifications.length === 0) {
    return null;
  }

  return (
    <section className="flex flex-col gap-4" aria-labelledby="updates-h">
      <h2 className="text-lg font-semibold" id="updates-h">Recent updates</h2>
      <ul className="flex flex-col gap-2 list-none p-0">
        {notifications.map((notification) => (
          <li key={notification.id} className="bg-gray-100 p-4">
            <div className="flex justify-between items-start mb-2">
              <p className="font-semibold text-sm">
                {notification.safe_preview_text}
              </p>
              {!notification.opened_at && (
                <span className="bg-black text-white text-xs px-2 py-0.5">New</span>
              )}
            </div>
            <p className="text-xs text-gray-600">
              Delivered {formatDateTime(notification.created_at)}
              {notification.opened_at ? ` · opened after sign-in` : ''}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
