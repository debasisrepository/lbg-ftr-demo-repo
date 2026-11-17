import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { RequireAuth } from './components/auth/RequireAuth';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './routes/login';
import { CaseListPage } from './routes/case-list';
import { ReportIssuePage } from './routes/report-issue';
import { CaseDetailPage } from './routes/case-detail';
import { ServiceStatusPage } from './routes/service-status';
import { LifelinePage } from './routes/lifeline';
import { ContinueChannelPage } from './routes/case-continue';
import { CaseHistoryPage } from './routes/case-history';
import { ProtectedActionPage } from './routes/case-action';
import { NotificationsPage } from './routes/notifications';
import { NotificationOpenPage } from './routes/notification-open';
import { ColleagueCaseRetrievalPage } from './routes/colleague-case-retrieval';

/**
 * Application router with public and protected routes
 */
export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Public service status - no auth required */}
        <Route 
          path="/status" 
          element={
            <AppLayout>
              <ServiceStatusPage />
            </AppLayout>
          } 
        />
        
        {/* Public lifeline - no auth required */}
        <Route 
          path="/lifeline" 
          element={
            <AppLayout>
              <LifelinePage />
            </AppLayout>
          } 
        />
        
        {/* Protected routes with layout */}
        <Route
          path="/cases"
          element={
            <RequireAuth>
              <AppLayout>
                <CaseListPage />
              </AppLayout>
            </RequireAuth>
          }
        />

        <Route
          path="/cases/:caseReference"
          element={
            <RequireAuth>
              <AppLayout>
                <CaseDetailPage />
              </AppLayout>
            </RequireAuth>
          }
        />
        
        <Route
          path="/cases/:caseReference/history"
          element={
            <RequireAuth>
              <AppLayout>
                <CaseHistoryPage />
              </AppLayout>
            </RequireAuth>
          }
        />
        
        <Route
          path="/cases/:caseReference/actions/:actionId"
          element={
            <RequireAuth>
              <AppLayout>
                <ProtectedActionPage />
              </AppLayout>
            </RequireAuth>
          }
        />
        
        <Route
          path="/cases/:caseReference/continue"
          element={
            <RequireAuth>
              <AppLayout>
                <ContinueChannelPage />
              </AppLayout>
            </RequireAuth>
          }
        />
        
        <Route
          path="/report"
          element={
            <RequireAuth>
              <AppLayout>
                <ReportIssuePage />
              </AppLayout>
            </RequireAuth>
          }
        />
        
        <Route
          path="/notifications"
          element={
            <RequireAuth>
              <AppLayout>
                <NotificationsPage />
              </AppLayout>
            </RequireAuth>
          }
        />
        
        <Route
          path="/notifications/open"
          element={
            <RequireAuth>
              <AppLayout>
                <NotificationOpenPage />
              </AppLayout>
            </RequireAuth>
          }
        />
        
        <Route
          path="/colleague/retrieve"
          element={
            <RequireAuth>
              <AppLayout>
                <ColleagueCaseRetrievalPage />
              </AppLayout>
            </RequireAuth>
          }
        />
        
        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/cases" replace />} />
        <Route path="*" element={<Navigate to="/cases" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
