import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './lib/auth-context';
import { RequireAuth } from './components/auth/RequireAuth';
import { SignInPage } from './pages/SignInPage';
import { AccountsOverviewPage } from './pages/AccountsOverviewPage';
import { PayeesPage } from './pages/PayeesPage';
import { PaymentEntryPage } from './pages/PaymentEntryPage';
import { PaymentReviewPage } from './pages/PaymentReviewPage';
import { PaymentOutcomePage } from './pages/PaymentOutcomePage';
import { PaymentSentPage } from './pages/PaymentSentPage';
import { PaymentFailedPage } from './pages/PaymentFailedPage';
import { PaymentWarningPage } from './pages/PaymentWarningPage';
import { PaymentPendingPage } from './pages/PaymentPendingPage';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<SignInPage />} />
          <Route
            path="/accounts"
            element={
              <RequireAuth>
                <AccountsOverviewPage />
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
            path="/payment-entry"
            element={
              <RequireAuth>
                <PaymentEntryPage />
              </RequireAuth>
            }
          />
          <Route
            path="/payment-review"
            element={
              <RequireAuth>
                <PaymentReviewPage />
              </RequireAuth>
            }
          />
          <Route
            path="/payment-outcome"
            element={
              <RequireAuth>
                <PaymentOutcomePage />
              </RequireAuth>
            }
          />
          <Route
            path="/payment-sent/:paymentId?"
            element={
              <RequireAuth>
                <PaymentSentPage />
              </RequireAuth>
            }
          />
          <Route
            path="/payment-failed/:paymentId?"
            element={
              <RequireAuth>
                <PaymentFailedPage />
              </RequireAuth>
            }
          />
          <Route
            path="/payment-warning"
            element={
              <RequireAuth>
                <PaymentWarningPage />
              </RequireAuth>
            }
          />
          <Route
            path="/payment-pending"
            element={
              <RequireAuth>
                <PaymentPendingPage />
              </RequireAuth>
            }
          />
          <Route path="/" element={<Navigate to="/accounts" replace />} />
          <Route path="*" element={<Navigate to="/accounts" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
