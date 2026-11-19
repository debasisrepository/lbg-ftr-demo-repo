/**
 * Main application component with routing
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './lib/auth-context';
import { LoginPage } from './pages/LoginPage';
import { StepUpPage } from './pages/StepUpPage';
import AccountsPage from './pages/AccountsPage';
import PayeesPage from './pages/PayeesPage';
import PaymentEntryPage from './pages/PaymentEntryPage';
import PaymentOutcomePage from './pages/PaymentOutcomePage';
import { RequireAuth } from './components/auth/RequireAuth';
import { AppLayout } from './components/layout/AppLayout';

function Dashboard() {
  return (
    <AppLayout>
      <div className="p-8">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p>You are logged in!</p>
      </div>
    </AppLayout>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/step-up" element={<StepUpPage />} />
          <Route
            path="/dashboard"
            element={
              <RequireAuth>
                <Dashboard />
              </RequireAuth>
            }
          />
          <Route
            path="/accounts"
            element={
              <RequireAuth>
                <AccountsPage />
              </RequireAuth>
            }
          />
          <Route
            path="/payees"
            element={
              <RequireAuth>
                <PayeesPage />
              </RequireAuth>
            }
          />
          <Route
            path="/payment/entry"
            element={
              <RequireAuth>
                <PaymentEntryPage />
              </RequireAuth>
            }
          />
          <Route
            path="/payment/outcome"
            element={
              <RequireAuth>
                <PaymentOutcomePage />
              </RequireAuth>
            }
          />
          <Route path="*" element={<div>404 Not Found</div>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
