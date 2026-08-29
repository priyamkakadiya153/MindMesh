import { create } from 'zustand';
import { AuthState, User, Organization } from './types';
import { applyOrganizationAccentColor } from '../../utils/theme';

interface AuthActions {
  setSession: (token: string, refreshToken: string, user: User) => void;
  clearSession: () => void;
  setOrganizations: (orgs: Organization[]) => void;
  setCurrentOrg: (org: Organization | null) => void;
  setLoading: (loading: boolean) => void;
}

const initialToken = localStorage.getItem('mindmesh_token') || localStorage.getItem('token') || null;
const initialRefreshToken = localStorage.getItem('mindmesh_refresh_token') || localStorage.getItem('refresh_token') || null;

export const useAuthStore = create<AuthState & AuthActions>((set, get) => ({
  user: null,
  token: initialToken,
  refreshToken: initialRefreshToken,
  currentOrg: null,
  organizations: [],
  isAuthenticated: false,
  loading: true,

  setSession: (token, refreshToken, user) => {
    if (token) {
      localStorage.setItem('mindmesh_token', token);
      localStorage.setItem('token', token);
    }
    if (refreshToken) {
      localStorage.setItem('mindmesh_refresh_token', refreshToken);
      localStorage.setItem('refresh_token', refreshToken);
    }
    set({ token, refreshToken, user, isAuthenticated: true, loading: false });
  },

  clearSession: () => {
    localStorage.removeItem('mindmesh_token');
    localStorage.removeItem('token');
    localStorage.removeItem('mindmesh_refresh_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('mindmesh_current_org_id');
    localStorage.removeItem('mindmesh_current_ws_id');
    localStorage.removeItem('mindmesh_current_proj_id');
    applyOrganizationAccentColor('#3B82F6');
    set({ 
      token: null, 
      refreshToken: null, 
      user: null, 
      currentOrg: null, 
      organizations: [], 
      isAuthenticated: false, 
      loading: false 
    });
  },

  setOrganizations: (organizations) => {
    set({ organizations });
    const user = get().user;
    const current = get().currentOrg;
    const savedOrgId = localStorage.getItem('mindmesh_current_org_id');

    if (organizations.length > 0) {
      const preferred = (savedOrgId && organizations.find(o => o.id === savedOrgId)) ||
        (user?.current_organization_id && organizations.find(o => o.id === user.current_organization_id)) ||
        null;
        
      if (preferred) {
        get().setCurrentOrg(preferred);
      } else if (!current || !organizations.find(o => o.id === current.id)) {
        get().setCurrentOrg(organizations[0]);
      }
    } else {
      get().setCurrentOrg(null);
    }
  },

  setCurrentOrg: (currentOrg) => {
    set({ currentOrg });
    if (currentOrg) {
      localStorage.setItem('mindmesh_current_org_id', currentOrg.id);
      const color = currentOrg.settings?.branding_color || (currentOrg as any).branding_color || '#3B82F6';
      applyOrganizationAccentColor(color);
    } else {
      localStorage.removeItem('mindmesh_current_org_id');
      applyOrganizationAccentColor('#3B82F6');
    }
  },

  setLoading: (loading) => {
    set({ loading });
  }
}));
