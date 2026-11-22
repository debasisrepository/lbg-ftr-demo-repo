import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { SignInPage } from './pages/SignInPage'
import { ProofPage } from './pages/ProofPage'
import { AccountsPage } from './pages/AccountsPage'
import { PayAndTransferPage } from './pages/PayAndTransferPage'
import { AddPayeePage } from './pages/AddPayeePage'
import EnterPaymentPage from './pages/EnterPaymentPage'
import ReviewApprovePage from './pages/ReviewApprovePage'
import PaymentOutcomePage from './pages/PaymentOutcomePage'
import ScamReportPage from './pages/ScamReportPage'
import IncidentReportPage from './pages/IncidentReportPage'
import StepUpPage from './pages/StepUpPage'
import { AuthProvider } from './lib/auth-context'
import { PaymentFlowProvider } from './features/payments/PaymentFlowProvider'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <PaymentFlowProvider>
          <Routes>
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/login" element={<SignInPage />} />
            <Route path="/proof" element={<ProofPage />} />
            <Route path="/step-up" element={<StepUpPage />} />
            <Route path="/accounts" element={<AccountsPage />} />
            <Route path="/pay-and-transfer" element={<PayAndTransferPage />} />
            <Route path="/add-payee" element={<AddPayeePage />} />
            <Route path="/pay" element={<EnterPaymentPage />} />
            <Route path="/payment/review" element={<ReviewApprovePage />} />
            <Route path="/payment/outcome" element={<PaymentOutcomePage />} />
            <Route path="/payment/scam-report" element={<ScamReportPage />} />
            <Route path="/support/incident-report" element={<IncidentReportPage />} />
          </Routes>
        </PaymentFlowProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
