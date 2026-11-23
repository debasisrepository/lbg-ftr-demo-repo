/**
 * Barrel export for all types
 */

export * from './auth';
export * from './accounts';
export * from './payments';
export * from './payees';

/**
 * Common types
 */

export interface ApiErrorResponse {
  detail: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
}

export interface ReadinessResponse {
  status: string;
  database: string;
  timestamp: string;
}

export interface CapabilityStatus {
  capability_name: string;
  status_value: string;
  cause_category: string | null;
  customer_message_code: string | null;
  recovery_guidance_code: string | null;
  effective_from: string;
}

export interface CapabilityStatusResponse {
  capabilities: CapabilityStatus[];
}
