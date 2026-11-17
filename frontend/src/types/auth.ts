export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  email: string;
  is_colleague: boolean;
}

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  is_colleague: boolean;
  customer_reference: string | null;
  brand: string | null;
}
