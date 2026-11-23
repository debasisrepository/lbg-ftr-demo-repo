/**
 * Authentication and user types
 */

export interface CustomerProfileRef {
  id: string;
  customer_party_id: string;
  ciam_subject_reference: string;
  display_name: string;
  profile_type: string;
  release_scope_status: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface User {
  customer_profile_ref_id: string;
  display_name: string;
  profile_type: string;
}

export interface LoginRequest {
  customer_party_id: string;
  passcode: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface SessionResponse {
  user: User;
  expires_at: string;
  last_activity_at: string;
}

export interface DeviceRegistration {
  id: string;
  customer_profile_ref_id: string;
  device_identifier_hash: string;
  mobile_platform: string;
  registration_status: string;
  ciam_subject_reference: string;
  registered_at: string;
  created_at: string;
  updated_at: string;
}
