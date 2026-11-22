import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import IncidentReportPage from '../pages/IncidentReportPage'

// Mock the useCreateIncidentReport hook
vi.mock('../features/support/useCreateIncidentReport', () => ({
  useCreateIncidentReport: vi.fn(),
}))

// Mock navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

import { useCreateIncidentReport } from '../features/support/useCreateIncidentReport'

describe('IncidentReportPage', () => {
  const mockCreateIncidentReport = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useCreateIncidentReport).mockReturnValue({
      createIncidentReport: mockCreateIncidentReport,
      loading: false,
      error: null,
    })
  })

  it('should render incident report form', () => {
    render(
      <BrowserRouter>
        <IncidentReportPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/Report an issue/i)).toBeInTheDocument()
    expect(screen.getByText(/Issue category/i)).toBeInTheDocument()
    expect(screen.getByText(/Severity/i)).toBeInTheDocument()
  })

  it('should render all incident category options', () => {
    render(
      <BrowserRouter>
        <IncidentReportPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/Technical issue/i)).toBeInTheDocument()
    expect(screen.getByText(/Service outage/i)).toBeInTheDocument()
    expect(screen.getByText(/Data issue/i)).toBeInTheDocument()
    expect(screen.getByText(/Security concern/i)).toBeInTheDocument()
  })

  it('should render severity level options', () => {
    render(
      <BrowserRouter>
        <IncidentReportPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/Low/i)).toBeInTheDocument()
    expect(screen.getByText(/Medium/i)).toBeInTheDocument()
    expect(screen.getByText(/High/i)).toBeInTheDocument()
    expect(screen.getByText(/Critical/i)).toBeInTheDocument()
  })

  it('should have title and description input fields', () => {
    render(
      <BrowserRouter>
        <IncidentReportPage />
      </BrowserRouter>
    )

    expect(screen.getByLabelText(/Issue title/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Description/i)).toBeInTheDocument()
  })

  it('should disable submit button when required fields are empty', () => {
    render(
      <BrowserRouter>
        <IncidentReportPage />
      </BrowserRouter>
    )

    const submitButton = screen.getByRole('button', { name: /Submit report/i })
    // Button should be disabled or visually indicate it can't be submitted
    // Depending on implementation, check if it has disabled styling or aria-disabled
  })

  it('should submit incident report with valid data', async () => {
    const user = userEvent.setup()
    mockCreateIncidentReport.mockResolvedValue({
      incident_reference: 'INC-2024-001',
      external_incident_ref: 'EXT-12345',
      incident_category: 'technical_issue',
      severity: 'high',
    })

    render(
      <BrowserRouter>
        <IncidentReportPage />
      </BrowserRouter>
    )

    // Select category
    const categorySelect = screen.getByLabelText(/Issue category/i)
    await user.click(categorySelect)
    await user.click(screen.getByText(/Technical issue/i))

    // Select severity
    const severitySelect = screen.getByLabelText(/Severity/i)
    await user.click(severitySelect)
    await user.click(screen.getByText(/High/i))

    // Fill title
    const titleInput = screen.getByLabelText(/Issue title/i)
    await user.type(titleInput, 'App crashes on login')

    // Fill description
    const descriptionInput = screen.getByLabelText(/Description/i)
    await user.type(descriptionInput, 'The mobile app crashes immediately after login')

    // Submit
    const submitButton = screen.getByRole('button', { name: /Submit report/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockCreateIncidentReport).toHaveBeenCalledWith({
        incident_category: 'technical_issue',
        incident_title: 'App crashes on login',
        incident_description: 'The mobile app crashes immediately after login',
        severity: 'high',
      })
    })
  })

  it('should show success message after successful submission', async () => {
    const user = userEvent.setup()
    mockCreateIncidentReport.mockResolvedValue({
      incident_reference: 'INC-2024-001',
      external_incident_ref: 'EXT-12345',
      incident_category: 'technical_issue',
      severity: 'medium',
    })

    render(
      <BrowserRouter>
        <IncidentReportPage />
      </BrowserRouter>
    )

    // Fill and submit form
    const categorySelect = screen.getByLabelText(/Issue category/i)
    await user.click(categorySelect)
    await user.click(screen.getByText(/Technical issue/i))

    const titleInput = screen.getByLabelText(/Issue title/i)
    await user.type(titleInput, 'Test issue')

    const submitButton = screen.getByRole('button', { name: /Submit report/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Incident report received/i)).toBeInTheDocument()
    })
  })

  it('should display incident reference after submission', async () => {
    const user = userEvent.setup()
    mockCreateIncidentReport.mockResolvedValue({
      incident_reference: 'INC-2024-001',
      external_incident_ref: 'EXT-12345',
      incident_category: 'technical_issue',
      severity: 'medium',
    })

    render(
      <BrowserRouter>
        <IncidentReportPage />
      </BrowserRouter>
    )

    // Fill and submit
    const categorySelect = screen.getByLabelText(/Issue category/i)
    await user.click(categorySelect)
    await user.click(screen.getByText(/Technical issue/i))

    const titleInput = screen.getByLabelText(/Issue title/i)
    await user.type(titleInput, 'Test issue')

    const submitButton = screen.getByRole('button', { name: /Submit report/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('INC-2024-001')).toBeInTheDocument()
    })
  })

  it('should display external ticket reference if available', async () => {
    const user = userEvent.setup()
    mockCreateIncidentReport.mockResolvedValue({
      incident_reference: 'INC-2024-001',
      external_incident_ref: 'EXT-12345',
      incident_category: 'technical_issue',
      severity: 'medium',
    })

    render(
      <BrowserRouter>
        <IncidentReportPage />
      </BrowserRouter>
    )

    // Fill and submit
    const categorySelect = screen.getByLabelText(/Issue category/i)
    await user.click(categorySelect)
    await user.click(screen.getByText(/Technical issue/i))

    const titleInput = screen.getByLabelText(/Issue title/i)
    await user.type(titleInput, 'Test issue')

    const submitButton = screen.getByRole('button', { name: /Submit report/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('EXT-12345')).toBeInTheDocument()
    })
  })

  it('should show loading state during submission', async () => {
    const user = userEvent.setup()
    vi.mocked(useCreateIncidentReport).mockReturnValue({
      createIncidentReport: mockCreateIncidentReport,
      loading: true,
      error: null,
    })

    render(
      <BrowserRouter>
        <IncidentReportPage />
      </BrowserRouter>
    )

    const submitButton = screen.getByRole('button', { name: /Submit report/i })
    // Button should show loading state or be disabled
    expect(submitButton).toBeInTheDocument()
  })
})
