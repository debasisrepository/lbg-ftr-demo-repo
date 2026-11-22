/**
 * Incident report categories (BR-OPS-008)
 */

export interface IncidentCategory {
  code: string
  label: string
  description: string
}

export const INCIDENT_CATEGORIES: IncidentCategory[] = [
  {
    code: 'technical_issue',
    label: 'Technical issue',
    description: 'App crashes, errors, or features not working',
  },
  {
    code: 'service_outage',
    label: 'Service outage',
    description: 'Unable to access services or complete actions',
  },
  {
    code: 'data_issue',
    label: 'Data issue',
    description: 'Incorrect balances, missing transactions, or data errors',
  },
  {
    code: 'security_concern',
    label: 'Security concern',
    description: 'Suspicious activity or security vulnerability',
  },
  {
    code: 'other',
    label: 'Other',
    description: 'Other operational issue',
  },
]

export const SEVERITY_LEVELS = [
  { code: 'low', label: 'Low - Minor inconvenience' },
  { code: 'medium', label: 'Medium - Affecting my banking' },
  { code: 'high', label: 'High - Cannot complete important tasks' },
  { code: 'critical', label: 'Critical - Unable to access my money' },
]
