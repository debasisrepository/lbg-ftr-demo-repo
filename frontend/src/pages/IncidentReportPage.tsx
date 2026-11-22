/**
 * Incident Report Page (BR-OPS-008)
 * Allows customers to report operational issues
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCreateIncidentReport } from '../features/support/useCreateIncidentReport'
import { INCIDENT_CATEGORIES, SEVERITY_LEVELS } from '../lib/incident-categories'

export default function IncidentReportPage() {
  const navigate = useNavigate()
  const { createIncidentReport, loading } = useCreateIncidentReport()

  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [selectedSeverity, setSelectedSeverity] = useState<string>('medium')
  const [title, setTitle] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [submitted, setSubmitted] = useState(false)
  const [incidentReference, setIncidentReference] = useState<string | null>(null)
  const [externalRef, setExternalRef] = useState<string | null>(null)

  const handleSubmit = async () => {
    if (!selectedCategory || !title) return

    const result = await createIncidentReport({
      incident_category: selectedCategory,
      incident_title: title,
      incident_description: description || undefined,
      severity: selectedSeverity,
    })

    if (result) {
      setIncidentReference(result.incident_reference)
      setExternalRef(result.external_incident_ref || null)
      setSubmitted(true)
    }
  }

  if (submitted && incidentReference) {
    return (
      <div className="min-h-screen bg-gray-100 flex flex-col">
        {/* Status Bar */}
        <div className="h-11 bg-white flex items-center px-6 font-semibold text-sm">
          9:41
        </div>

        {/* Content */}
        <div className="flex-1 bg-white px-6 py-8 flex flex-col">
          {/* Success Icon */}
          <div
            className="w-18 h-18 border-[3px] border-black rounded-full flex items-center justify-center my-6"
            aria-hidden="true"
          >
            <svg
              viewBox="0 0 24 24"
              className="w-10 h-10 stroke-black fill-none stroke-[3]"
            >
              <path d="M4 12l5 5 11-11" strokeLinecap="square" />
            </svg>
          </div>

          <h2 className="text-[28px] leading-9 font-semibold mb-3">
            Incident report received
          </h2>

          <p className="text-base leading-6 text-gray-700 mb-6">
            Thank you for reporting this issue. Our technical team will
            investigate and we&apos;ll contact you with updates.
          </p>

          {/* Incident Reference */}
          <div className="border border-gray-400 bg-gray-100 px-4 py-3 mb-4 text-sm leading-5 flex justify-between">
            <span>Incident reference</span>
            <span className="font-semibold">{incidentReference}</span>
          </div>

          {externalRef && (
            <div className="border border-gray-400 bg-gray-100 px-4 py-3 mb-4 text-sm leading-5 flex justify-between">
              <span>Support ticket</span>
              <span className="font-semibold">{externalRef}</span>
            </div>
          )}

          {/* Next Steps */}
          <div className="border border-gray-400 border-l-4 border-l-black bg-gray-100 px-4 py-3 mb-4 text-sm leading-5">
            <p className="font-semibold text-base leading-6 mb-1">Next steps</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Save your incident reference for future contact</li>
              <li>We&apos;ll update you on investigation progress</li>
              <li>Check notifications for updates</li>
              <li>
                For urgent issues: 0345 300 0000 (Monday-Friday, 9am-5pm)
              </li>
            </ul>
          </div>

          <div className="flex-1" />

          <button
            onClick={() => navigate('/accounts')}
            className="w-full min-h-[52px] px-4 border-2 border-black bg-black text-white font-semibold text-base hover:bg-gray-900 mt-3"
          >
            Back to accounts
          </button>
        </div>
      </div>
    )
  }

  // const selectedCategoryObj = INCIDENT_CATEGORIES.find(
  //   (cat) => cat.code === selectedCategory
  // )

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Status Bar */}
      <div className="h-11 bg-white flex items-center px-6 font-semibold text-sm">
        9:41
      </div>

      {/* Top Bar */}
      <div className="min-h-12 bg-white flex items-center px-2">
        <button
          onClick={() => navigate(-1)}
          className="w-11 h-11 flex items-center justify-center"
          aria-label="Back"
        >
          <svg
            viewBox="0 0 24 24"
            className="w-6 h-6 stroke-current fill-none stroke-2"
            aria-hidden="true"
          >
            <path d="M19 12H5M11 5l-7 7 7 7" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 bg-white px-6 py-2 flex flex-col">
        <h2 className="text-[28px] leading-9 font-semibold mt-4 mb-1">
          Report an issue
        </h2>
        <p className="text-base leading-6 text-gray-700 mb-6">
          Tell us about any technical or service issues you&apos;re
          experiencing. This helps us improve the app for everyone.
        </p>

        {/* Category Selection */}
        <div className="mb-6">
          <label className="block text-sm leading-5 font-semibold mb-2">
            What type of issue are you experiencing? *
          </label>
          <div className="space-y-2">
            {INCIDENT_CATEGORIES.map((category) => (
              <label
                key={category.code}
                className="flex items-start space-x-2 cursor-pointer p-3 border border-gray-400 bg-gray-50 hover:bg-gray-100"
              >
                <input
                  type="radio"
                  name="incident-category"
                  value={category.code}
                  checked={selectedCategory === category.code}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-4 h-4 mt-1"
                />
                <div className="flex-1">
                  <div className="text-sm font-semibold">{category.label}</div>
                  <div className="text-sm text-gray-600">
                    {category.description}
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Title */}
        <div className="mb-6">
          <label
            htmlFor="title"
            className="block text-sm leading-5 font-semibold mb-2"
          >
            Brief summary *
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={255}
            placeholder="e.g., Cannot view my savings account balance"
            className="w-full border border-gray-400 bg-gray-100 px-4 py-3 text-base"
          />
        </div>

        {/* Description */}
        <div className="mb-6">
          <label
            htmlFor="description"
            className="block text-sm leading-5 font-semibold mb-2"
          >
            Full description (optional)
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            maxLength={2000}
            placeholder="Provide any additional details that might help us understand the issue..."
            className="w-full border border-gray-400 bg-gray-100 px-4 py-3 text-base resize-none"
          />
          <p className="text-xs text-gray-600 mt-1">
            {description.length} / 2000 characters
          </p>
        </div>

        {/* Severity */}
        <div className="mb-6">
          <label className="block text-sm leading-5 font-semibold mb-2">
            How is this affecting you?
          </label>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="w-full border border-gray-400 bg-gray-100 px-4 py-3 text-base"
          >
            {SEVERITY_LEVELS.map((level) => (
              <option key={level.code} value={level.code}>
                {level.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1" />

        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          disabled={!selectedCategory || !title || loading}
          className={`w-full min-h-[52px] px-4 border-2 font-semibold text-base mt-3 ${
            !selectedCategory || !title || loading
              ? 'border-gray-300 bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'border-black bg-black text-white hover:bg-gray-900'
          }`}
        >
          {loading ? 'Submitting...' : 'Report issue'}
        </button>

        <button
          onClick={() => navigate('/accounts')}
          disabled={loading}
          className="w-full min-h-[52px] px-4 border-2 border-black bg-white text-black font-semibold text-base hover:bg-gray-50 mt-3"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
