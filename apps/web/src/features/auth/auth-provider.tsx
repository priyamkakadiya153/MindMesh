import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuthStore } from './auth-store';
import * as api from './api';
import { User, Organization } from './types';
import { useWorkspaceStore } from '../workspace/store';
import { useNavigationStore } from '../navigation/store';

interface AuthContextType {
  user: User | null;
  token: string | null;
  currentOrg: Organization | null;
  organizations: Organization[];
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithFirebaseToken: (idToken: string) => Promise<void>;
  sendPhoneOtp: (phoneNumber: string) => Promise<{ status: string; message: string; email_masked: string; expires_in_seconds: number; resend_cooldown_seconds: number }>;
  resendPhoneOtp: (phoneNumber: string) => Promise<{ status: string; message: string; email_masked: string; expires_in_seconds: number; resend_cooldown_seconds: number }>;
  verifyPhoneOtp: (phoneNumber: string, code: string) => Promise<void>;
  register: (user_in: any) => Promise<any>;
  registerInitiate: (user_in: any) => Promise<{ status: string; message: string; email_masked: string; registration_token: string; expires_in_seconds: number; resend_cooldown_seconds: number }>;
  registerResendOtp: (registrationToken: string) => Promise<{ status: string; message: string; email_masked: string; registration_token: string; resend_cooldown_seconds: number }>;
  registerVerifyOtp: (registrationToken: string, code: string) => Promise<void>;
  logout: () => Promise<void>;
  switchOrganization: (org: Organization) => Promise<void>;
  createOrg: (name: string, slug: string) => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const store = useAuthStore();
  const [init, setInit] = useState(false);

  const handlePostAuthSetup = async (authToken: string, user: User) => {
    try {
      // 1. Restore & Sync Organizations
      const orgs = await api.getOrganizations(authToken);
      store.setOrganizations(orgs);

      const savedOrgId = localStorage.getItem('mindmesh_current_org_id');
      const activeOrg = (savedOrgId && orgs.find(o => o.id === savedOrgId)) ||
        (user.current_organization_id && orgs.find(o => o.id === user.current_organization_id)) ||
        orgs[0] ||
        null;

      if (activeOrg) {
        store.setCurrentOrg(activeOrg);
        const wsStore = useWorkspaceStore.getState();
        await wsStore.fetchWorkspaces(authToken, activeOrg.id);
      }

      // 2. Restore & Sync Theme (Order: localStorage -> User profile -> System)
      const navStore = useNavigationStore.getState();
      const localTheme = localStorage.getItem('mindmesh_theme');
      let themeToApply: string | null = null;

      if (localTheme && (localTheme === 'light' || localTheme === 'dark' || localTheme === 'system')) {
        themeToApply = localTheme;
      } else if (user.theme && (user.theme === 'light' || user.theme === 'dark' || user.theme === 'system')) {
        themeToApply = user.theme;
      } else {
        themeToApply = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }

      navStore.setTheme(themeToApply as any);

    } catch (e) {
      console.warn("Post-auth tenant initialization warning:", e);
    }
  };

  const refreshProfile = async () => {
    const rToken = store.refreshToken || localStorage.getItem('mindmesh_refresh_token') || localStorage.getItem('refresh_token') || '';
    if (!rToken) {
      store.clearSession();
      return;
    }
    try {
      store.setLoading(true);
      const res: any = await api.refresh(rToken);
      const user = await api.getCurrentUser(res.access_token);
      store.setSession(res.access_token, res.refresh_token, user);
      await handlePostAuthSetup(res.access_token, user);
    } catch (err) {
      console.warn("Refresh session failed:", err);
      store.clearSession();
    } finally {
      store.setLoading(false);
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      store.setLoading(true);
      const existingToken = localStorage.getItem('mindmesh_token') || localStorage.getItem('token');
      const rToken = localStorage.getItem('mindmesh_refresh_token') || localStorage.getItem('refresh_token');

      if (existingToken) {
        try {
          const user = await api.getCurrentUser(existingToken);
          store.setSession(existingToken, rToken || '', user);
          await handlePostAuthSetup(existingToken, user);
        } catch (e) {
          console.warn("Token validation failed, attempting refresh...", e);
          await refreshProfile();
        }
      } else if (rToken) {
        await refreshProfile();
      } else {
        store.clearSession();
      }
      setInit(true);
      store.setLoading(false);
    };
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    store.setLoading(true);
    try {
      const res: any = await api.login(email, password);
      store.setSession(res.access_token, res.refresh_token, res.user);
      await handlePostAuthSetup(res.access_token, res.user);
    } finally {
      store.setLoading(false);
    }
  };

  const loginWithFirebaseToken = async (idToken: string) => {
    store.setLoading(true);
    try {
      const res: any = await api.loginWithFirebaseToken(idToken);
      store.setSession(res.access_token, res.refresh_token, res.user);
      await handlePostAuthSetup(res.access_token, res.user);
    } finally {
      store.setLoading(false);
    }
  };

  const sendPhoneOtp = async (phoneNumber: string) => {
    return await api.sendPhoneOtp(phoneNumber);
  };

  const resendPhoneOtp = async (phoneNumber: string) => {
    return await api.resendPhoneOtp(phoneNumber);
  };

  const verifyPhoneOtp = async (phoneNumber: string, code: string) => {
    store.setLoading(true);
    try {
      const res: any = await api.verifyPhoneOtp(phoneNumber, code);
      store.setSession(res.access_token, res.refresh_token, res.user);
      await handlePostAuthSetup(res.access_token, res.user);
    } finally {
      store.setLoading(false);
    }
  };

  const register = async (user_in: any) => {
    store.setLoading(true);
    try {
      return await api.register(user_in);
    } finally {
      store.setLoading(false);
    }
  };

  const registerInitiate = async (user_in: any) => {
    store.setLoading(true);
    try {
      return await api.registerInitiate(user_in);
    } finally {
      store.setLoading(false);
    }
  };

  const registerResendOtp = async (registrationToken: string) => {
    return await api.registerResendOtp(registrationToken);
  };

  const registerVerifyOtp = async (registrationToken: string, code: string) => {
    store.setLoading(true);
    try {
      const res: any = await api.registerVerifyOtp(registrationToken, code);
      store.setSession(res.access_token, res.refresh_token, res.user);
      await handlePostAuthSetup(res.access_token, res.user);
    } finally {
      store.setLoading(false);
    }
  };

  const logout = async () => {
    if (store.refreshToken) {
      await api.logout(store.refreshToken).catch(() => {});
    }
    store.clearSession();
  };

  const switchOrganization = async (org: Organization) => {
    if (!store.token) return;
    store.setLoading(true);
    try {
      await api.updateCurrentOrganization(store.token, org.id);
      
      const user = await api.getCurrentUser(store.token);
      store.setSession(store.token, store.refreshToken || '', user);
      
      const orgs = await api.getOrganizations(store.token);
      store.setOrganizations(orgs);
      
      const preferred = orgs.find(o => o.id === org.id);
      if (preferred) {
        store.setCurrentOrg(preferred);
      }
      
      const wsStore = useWorkspaceStore.getState();
      await wsStore.fetchWorkspaces(store.token, org.id);
      
      const workspaces = wsStore.workspaces;
      if (workspaces.length > 0) {
        const matchingWs = workspaces.find(w => w.id === user.current_workspace_id) || workspaces[0];
        wsStore.selectWorkspace(matchingWs);
      } else {
        wsStore.selectWorkspace(null as any);
      }
    } catch (err) {
      console.error("Failed to switch organization:", err);
    } finally {
      store.setLoading(false);
    }
  };

  const createOrg = async (name: string, slug: string) => {
    if (!store.token) return;
    store.setLoading(true);
    try {
      await api.createOrganization(store.token, name, slug);
      const orgs = await api.getOrganizations(store.token);
      store.setOrganizations(orgs);
    } finally {
      store.setLoading(false);
    }
  };

  if (!init) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950 text-white">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-violet-500 border-t-transparent"></div>
          <span className="text-sm font-medium text-slate-400">Loading Session...</span>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{
        user: store.user,
        token: store.token,
        currentOrg: store.currentOrg,
        organizations: store.organizations,
        isAuthenticated: store.isAuthenticated,
        loading: store.loading,
        login,
        loginWithFirebaseToken,
        sendPhoneOtp,
        resendPhoneOtp,
        verifyPhoneOtp,
        register,
        registerInitiate,
        registerResendOtp,
        registerVerifyOtp,
        logout,
        switchOrganization,
        createOrg,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
