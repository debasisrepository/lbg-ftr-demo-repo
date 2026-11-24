import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './lib/auth-context'
import { RequireAuth } from './components/auth/RequireAuth'
import { AppShell } from './components/layout/AppShell'
import { SignInPage } from './pages/SignInPage'
import { LandingPage } from './pages/LandingPage'
import { WorkQueuePage } from './pages/WorkQueuePage'
import { Customer360Page } from './pages/Customer360Page'
import { PromiseToPayPage } from './pages/PromiseToPayPage'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<SignInPage />} />
          
          {/* Protected routes */}
          <Route
            path="/*"
            element={
              <RequireAuth>
                <AppShell>
                  <Routes>
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/queue" element={<WorkQueuePage />} />
                    <Route path="/customer/:customerId" element={<Customer360Page />} />
                    <Route path="/promise/new" element={<PromiseToPayPage />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </AppShell>
              </RequireAuth>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
