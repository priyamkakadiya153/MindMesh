export interface User {
  id: string;
  email: string;
  username: string;
  first_name?: string | null;
  last_name?: string | null;
  phone_number?: string | null;
  avatar_url?: string | null;
  bio?: string | null;
  timezone?: string | null;
  language?: string | null;
  theme?: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_phone_verified?: boolean;
  two_factor_enabled?: boolean;
  last_login_at?: string | null;
  current_organization_id?: string | null;
  organization_id?: string | null;
  current_workspace_id?: string | null;
}

export interface OrganizationSettings {
  default_language: string;
  timezone: string;
  theme: string;
  branding_color: string;
  allow_public_invites: boolean;
  allow_guest_access: boolean;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  role: string;
  logo_url?: string | null;
  description?: string | null;
  website?: string | null;
  industry?: string | null;
  country?: string | null;
  timezone?: string;
  language?: string;
  owner_id?: string | null;
  status?: string;
  visibility?: string;
  is_personal?: boolean;
  settings?: OrganizationSettings | null;
  created_at?: string;
}

export interface DeviceSession {
  id: string;
  device: string;
  ip_address?: string | null;
  user_agent?: string | null;
  created_at: string;
  last_activity: string;
  expires_at: string;
  is_current: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  organizations: Organization[];
  currentOrg: Organization | null;
}
