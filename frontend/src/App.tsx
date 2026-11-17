import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './lib/auth-context';
import { RequireAuth } from './components/auth/RequireAuth';
import { LoginPage } from './pages/LoginPage';
import { Layout } from './components/layout/Layout';
import { ResolvePage } from './pages/ResolvePage';
import { ResolveSessionPage } from './pages/ResolveSessionPage';
import { CaseConfirmationPage } from './pages/CaseConfirmationPage';
import { MyCasesPage } from './pages/MyCasesPage';
import { CaseDetailPage } from './pages/CaseDetailPage';
import { ColleagueCasePage } from './pages/ColleagueCasePage';

function DashboardPage() {
  return (
    <div>
      <h1 className="font-head text-3xl font-bold text-ink mb-s4">Dashboard</h1>
      <p className="text-muted">Welcome to Clear Path.</p>
    </div>
  );
}

function ColleagueCasesPage() {
  return (
    <div>
      <h1 className="font-head text-3xl font-bold text-ink mb-s4">Team Cases</h1>
      <p className="text-muted">Team cases will appear here.</p>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          
          <Route
            path="/"
            element={
              <RequireAuth>
                <Layout>
                  <DashboardPage />
                </Layout>
              </RequireAuth>
            }
          />
          
          <Route
            path="/cases"
            element={
              <RequireAuth>
                <MyCasesPage />
              </RequireAuth>
            }
          />
          
          <Route
            path="/cases/:caseId"
            element={
              <RequireAuth>
                <CaseDetailPage />
              </RequireAuth>
            }
          />
          
          <Route
            path="/case-confirmation"
            element={
              <RequireAuth>
                <CaseConfirmationPage />
              </RequireAuth>
            }
          />
          
          <Route
            path="/colleague/cases"
            element={
              <RequireAuth>
                <Layout>
                  <ColleagueCasesPage />
                </Layout>
              </RequireAuth>
            }
          />
          
          <Route
            path="/colleague/cases/:caseId"
            element={
              <RequireAuth>
                <ColleagueCasePage />
              </RequireAuth>
            }
          />
          
          <Route
            path="/resolve"
            element={
              <RequireAuth>
                <ResolvePage />
              </RequireAuth>
            }
          />
          
          <Route
            path="/resolve/:sessionId"
            element={
              <RequireAuth>
                <ResolveSessionPage />
              </RequireAuth>
            }
          />
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
