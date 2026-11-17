import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../lib/api-client';

/**
 * Notification deep-link entry point
 * Handles /notifications/open?token=xxx flow
 */
export function NotificationOpenPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (!token) {
      setError('Missing notification token');
      return;
    }

    // Call the backend endpoint to mark notification as opened and get redirect target
    apiClient
      .post<{ deep_link_target: string }>('/notifications/open', { token })
      .then((response) => {
        // Redirect to the deep link target
        navigate(response.deep_link_target, { replace: true });
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to open notification');
      });
  }, [searchParams, navigate]);

  return (
    <div className="max-w-4xl mx-auto p-6 flex flex-col gap-6">
      <h1 className="cds--productive-heading-05">Opening Notification</h1>
      
      {error ? (
        <p className="text-red-600">{error}</p>
      ) : (
        <p>Redirecting...</p>
      )}
    </div>
  );
}
