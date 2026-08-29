import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { useAuthStore } from '../../features/auth/auth-store';
import { applyOrganizationAccentColor } from '../../utils/theme';
import { useNavigationStore } from '../../features/navigation/store';
import { useWorkspaceStore } from '../../features/workspace/store';
import { apiClient } from '../../lib/api-client';
import { formatTimestamp } from '../../utils/date';
import { EmptyState } from '../../shared/components/EmptyState';
import {
  Settings, User, Bell, Shield, Palette, Globe, Clock, Lock, Key,
  Check, Save, RefreshCw, AlertCircle, FileText, Activity, Moon, Sun, Monitor, Loader2, Sliders,
  Info, Search, ChevronLeft, ChevronRight, Eye, X, Database, Sparkles, Cpu, Layers, Bot, HardDrive, Users, Briefcase
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { token, currentOrg, user: currentUser, refreshProfile } = useAuth();
  const { currentWorkspace, selectWorkspace } = useWorkspaceStore();

  const [activeTab, setActiveTab] = useState<'profile' | 'notifications' | 'org_branding' | 'workspace' | 'security_audit'>('profile');

  // RBAC Permission Checks
  const userRole = (currentOrg?.role || 'member').toLowerCase();
  const canEditOrg = ['owner', 'admin', 'super_admin', 'org_admin'].includes(userRole);
  const canEditWorkspace = canEditOrg || (currentWorkspace?.owner_id === currentUser?.id);

  // Tab 1: Profile Form State
  const [username, setUsername] = useState(currentUser?.username || '');
  const [email, setEmail] = useState(currentUser?.email || '');
  const [mobile, setMobile] = useState(currentUser?.phone_number || (currentUser as any)?.mobile || '');
  const [avatarUrl, setAvatarUrl] = useState(currentUser?.avatar_url || '');
  const [theme, setTheme] = useState(currentUser?.theme || 'dark');
  const [language, setLanguage] = useState(currentUser?.language || 'en');
  const [timezone, setTimezone] = useState(currentUser?.timezone || 'UTC');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  // Tab 2: Notification Preferences
  const [emailNotifs, setEmailNotifs] = useState(true);
  const [inAppNotifs, setInAppNotifs] = useState(true);
  const [mentions, setMentions] = useState(true);
  const [projectUpdates, setProjectUpdates] = useState(true);

  // Tab 3: Organization & Branding State
  const [orgName, setOrgName] = useState(currentOrg?.name || '');
  const [orgDescription, setOrgDescription] = useState(currentOrg?.description || '');
  const [orgWebsite, setOrgWebsite] = useState(currentOrg?.website || '');
  const [orgLogoUrl, setOrgLogoUrl] = useState(currentOrg?.logo_url || '');
  const [orgBrandingColor, setOrgBrandingColor] = useState(currentOrg?.settings?.branding_color || '#6366F1');

  // Tab 4: Workspace Config State
  const [wsName, setWsName] = useState(currentWorkspace?.name || '');
  const [wsDescription, setWsDescription] = useState(currentWorkspace?.description || '');
  const [wsVisibility, setWsVisibility] = useState('private');
  const [wsDefaultDashboard, setWsDefaultDashboard] = useState('overview');
  const [wsTimezone, setWsTimezone] = useState('UTC');
  const [wsLanguage, setWsLanguage] = useState('en');
  const [wsDefaultAiModel, setWsDefaultAiModel] = useState('gemini-2.5-flash');
  const [wsAutoIndex, setWsAutoIndex] = useState(true);
  const [wsEnableSemanticSearch, setWsEnableSemanticSearch] = useState(true);
  const [wsEnableAiChat, setWsEnableAiChat] = useState(true);
  const [wsColor, setWsColor] = useState('#3B82F6');
  const [wsStats, setWsStats] = useState({ storageBytes: 0, memberCount: 1, projectCount: 0, documentCount: 0 });

  // Tab 5: Security Policies & Audit State
  const [allowPublicInvites, setAllowPublicInvites] = useState(false);
  const [allowGuestAccess, setAllowGuestAccess] = useState(true);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditSearch, setAuditSearch] = useState('');
  const [auditActionFilter, setAuditActionFilter] = useState('all');
  const [auditPage, setAuditPage] = useState(1);
  const [selectedAuditLog, setSelectedAuditLog] = useState<any | null>(null);

  // General Status Messages & Submission
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Sync user profile when currentUser is loaded or user ID changes
  useEffect(() => {
    if (currentUser) {
      setUsername(currentUser.username || '');
      setEmail(currentUser.email || '');
      setMobile(currentUser.phone_number || (currentUser as any)?.mobile || '');
      setAvatarUrl(currentUser.avatar_url || '');
      if (currentUser.theme) setTheme(currentUser.theme);
      if (currentUser.language) setLanguage(currentUser.language);
      if (currentUser.timezone) setTimezone(currentUser.timezone);
    }
  }, [currentUser?.id]);

  // Sync organization fields when currentOrg changes
  useEffect(() => {
    if (currentOrg) {
      setOrgName(currentOrg.name || '');
      setOrgDescription(currentOrg.description || '');
      setOrgWebsite(currentOrg.website || '');
      setOrgLogoUrl(currentOrg.logo_url || '');
      if (currentOrg.settings?.branding_color) {
        setOrgBrandingColor(currentOrg.settings.branding_color);
      }
    }
  }, [currentOrg?.id]);

  // Sync workspace fields when currentWorkspace changes
  useEffect(() => {
    if (currentWorkspace) {
      setWsName(currentWorkspace.name || '');
      setWsDescription(currentWorkspace.description || '');
      setWsColor(currentWorkspace.color || '#3B82F6');
    }
  }, [currentWorkspace?.id]);

  // Fetch tab-specific data
  useEffect(() => {
    if (token) {
      fetchUserSettings();
      if (currentOrg) {
        fetchOrgSettings();
      }
      if (currentWorkspace) {
        fetchWorkspaceSettingsAndStats();
      }
      if (activeTab === 'security_audit') {
        fetchAuditLogs();
      }
    }
  }, [token, currentOrg?.id, currentWorkspace?.id, activeTab]);

  const fetchUserSettings = async () => {
    if (!token) return;
    try {
      const res = await apiClient.get('/settings');
      const data = res.data;
      if (data) {
        if (data.theme) setTheme(data.theme);
        if (data.language) setLanguage(data.language);
        if (data.timezone) setTimezone(data.timezone);
        setEmailNotifs(data.email_notifications ?? true);
        setInAppNotifs(data.in_app_notifications ?? true);
        setMentions(data.mentions ?? true);
        setProjectUpdates(data.project_updates ?? true);
      }
    } catch (err) {
      console.error("Failed to load user settings:", err);
    }
  };

  const fetchOrgSettings = async () => {
    if (!token || !currentOrg) return;
    try {
      const res = await apiClient.get(`/organizations/${currentOrg.id}/settings`);
      if (res.data) {
        setOrgBrandingColor(res.data.branding_color || '#6366F1');
        setAllowPublicInvites(res.data.allow_public_invites ?? false);
        setAllowGuestAccess(res.data.allow_guest_access ?? true);
      }
    } catch (err) {
      console.error("Failed to load organization settings:", err);
    }
  };

  const fetchWorkspaceSettingsAndStats = async () => {
    if (!token || !currentOrg || !currentWorkspace) return;
    try {
      const [settingsRes, membersRes, projectsRes, docsRes] = await Promise.all([
        apiClient.get(`/workspaces/${currentWorkspace.id}/settings`).catch(() => null),
        apiClient.get(`/workspaces/${currentWorkspace.id}/members`).catch(() => null),
        apiClient.get(`/projects?workspace_id=${currentWorkspace.id}`).catch(() => null),
        apiClient.get(`/documents?workspace_id=${currentWorkspace.id}`).catch(() => null)
      ]);

      if (settingsRes?.data) {
        const s = settingsRes.data;
        if (s.timezone) setWsTimezone(s.timezone);
        if (s.language) setWsLanguage(s.language);
        if (s.default_dashboard) setWsDefaultDashboard(s.default_dashboard);
        if (s.visibility) setWsVisibility(s.visibility);
        if (s.default_ai_model) setWsDefaultAiModel(s.default_ai_model);
        setWsAutoIndex(s.auto_index_files ?? true);
        setWsEnableSemanticSearch(s.enable_semantic_search ?? true);
        setWsEnableAiChat(s.enable_ai_chat ?? true);
      }

      const memberList = Array.isArray(membersRes?.data) ? membersRes.data : [];
      const projectList = Array.isArray(projectsRes?.data) ? projectsRes.data : [];
      const docList = Array.isArray(docsRes?.data) ? docsRes.data : [];
      const totalBytes = docList.reduce((acc: number, d: any) => acc + (Number(d.size_bytes || d.size || 0)), 0);

      setWsStats({
        storageBytes: totalBytes,
        memberCount: memberList.length || 1,
        projectCount: projectList.length || 0,
        documentCount: docList.length || 0
      });
    } catch (err) {
      console.error("Failed to load workspace settings/stats:", err);
    }
  };

  const fetchAuditLogs = async () => {
    if (!token || !currentOrg) return;
    try {
      const res = await apiClient.get('/audit', {
        headers: { 'X-Organization-ID': currentOrg.id }
      });
      setAuditLogs(res.data || []);
    } catch (err) {
      console.error("Failed to load audit logs:", err);
    }
  };

  // Tab 1 Save Handler (Profile & Preferences)
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setIsSubmitting(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const profileRes = await apiClient.patch('/profile', {
        username,
        email,
        mobile,
        avatar_url: avatarUrl,
        current_password: currentPassword || undefined,
        new_password: newPassword || undefined,
      });

      const settingsRes = await apiClient.patch('/settings', {
        theme,
        language,
        timezone,
        email_notifications: emailNotifs,
        in_app_notifications: inAppNotifs,
        mentions,
        project_updates: projectUpdates,
      });

      // Update global navigation theme & DOM
      useNavigationStore.getState().setTheme(theme as any);

      // Update session user in authStore
      const updatedProfile = profileRes.data;
      const updatedSettings = settingsRes.data;
      const rToken = useAuthStore.getState().refreshToken || localStorage.getItem('refresh_token') || '';

      if (currentUser && updatedProfile) {
        useAuthStore.getState().setSession(token, rToken, {
          ...currentUser,
          username: updatedProfile.username || username,
          email: updatedProfile.email || email,
          phone_number: updatedProfile.phone_number || updatedProfile.mobile || mobile,
          avatar_url: updatedProfile.avatar_url ?? avatarUrl,
          theme: updatedSettings?.theme || theme,
          language: updatedSettings?.language || language,
          timezone: updatedSettings?.timezone || timezone,
        });
      }

      setSuccessMsg('Profile and preferences updated successfully!');
      setCurrentPassword('');
      setNewPassword('');
    } catch (err: any) {
      console.error('Save profile error:', err);
      const detail = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to update profile';
      setErrorMsg(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Tab 2 Save Handler (Notification Controls)
  const handleSaveNotifications = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setIsSubmitting(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const res = await apiClient.patch('/settings', {
        email_notifications: emailNotifs,
        in_app_notifications: inAppNotifs,
        mentions,
        project_updates: projectUpdates,
      });

      if (currentUser) {
        const rToken = useAuthStore.getState().refreshToken || localStorage.getItem('refresh_token') || '';
        useAuthStore.getState().setSession(token, rToken, {
          ...currentUser,
          in_app_notifications: inAppNotifs,
        } as any);
      }

      setSuccessMsg('Notification preferences saved successfully!');
    } catch (err: any) {
      console.error('Save notifications error:', err);
      const detail = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to update notification settings';
      setErrorMsg(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Tab 3 Save Handler (Organization Branding)
  const handleSaveOrgBranding = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !currentOrg) return;
    if (!canEditOrg) {
      setErrorMsg('You need Organization Admin or Owner permission to modify organization branding.');
      return;
    }
    setIsSubmitting(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const orgRes = await apiClient.patch(`/organizations/${currentOrg.id}`, {
        name: orgName,
        description: orgDescription,
        website: orgWebsite,
        logo_url: orgLogoUrl
      });

      const settingsRes = await apiClient.patch(`/organizations/${currentOrg.id}/settings`, {
        branding_color: orgBrandingColor
      });

      // Apply CSS primary accent token dynamically if provided
      if (orgBrandingColor) {
        applyOrganizationAccentColor(orgBrandingColor);
      }

      await refreshProfile();
      setSuccessMsg('Organization branding updated successfully!');
    } catch (err: any) {
      console.error('Save organization branding error:', err);
      const detail = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to update organization branding';
      setErrorMsg(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Tab 4 Save Handler (Workspace Config)
  const handleSaveWorkspaceConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !currentOrg || !currentWorkspace) return;
    if (!canEditWorkspace) {
      setErrorMsg('You need Organization Admin or Workspace Owner permission to modify workspace configurations.');
      return;
    }
    setIsSubmitting(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const wsRes = await apiClient.patch(`/workspaces/${currentWorkspace.id}`, {
        name: wsName,
        description: wsDescription,
        color: wsColor
      });

      const settingsRes = await apiClient.patch(`/workspaces/${currentWorkspace.id}/settings`, {
        visibility: wsVisibility,
        default_dashboard: wsDefaultDashboard,
        timezone: wsTimezone,
        language: wsLanguage,
        default_ai_model: wsDefaultAiModel,
        auto_index_files: wsAutoIndex,
        enable_semantic_search: wsEnableSemanticSearch,
        enable_ai_chat: wsEnableAiChat
      });

      if (wsRes.data) {
        selectWorkspace(wsRes.data);
      }
      setSuccessMsg('Workspace configuration updated successfully!');
    } catch (err: any) {
      console.error('Save workspace config error:', err);
      const detail = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to update workspace settings';
      setErrorMsg(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Tab 5 Save Handler (Security Policies)
  const handleSaveSecurity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !currentOrg) return;
    if (!canEditOrg) {
      setErrorMsg('You need Organization Admin or Owner permission to modify security policies.');
      return;
    }
    setIsSubmitting(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      await apiClient.patch(`/organizations/${currentOrg.id}/settings`, {
        allow_public_invites: allowPublicInvites,
        allow_guest_access: allowGuestAccess
      });
      setSuccessMsg('Security policies updated successfully!');
    } catch (err: any) {
      console.error('Save security policies error:', err);
      const detail = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to update security policies';
      setErrorMsg(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Audit Logs Filtering & Pagination Logic
  const filteredAuditLogs = useMemo(() => {
    return auditLogs.filter((log) => {
      const matchSearch =
        !auditSearch ||
        log.action?.toLowerCase().includes(auditSearch.toLowerCase()) ||
        log.resource_type?.toLowerCase().includes(auditSearch.toLowerCase()) ||
        JSON.stringify(log.details || {}).toLowerCase().includes(auditSearch.toLowerCase());

      const matchAction =
        auditActionFilter === 'all' ||
        log.action?.toLowerCase().startsWith(auditActionFilter.toLowerCase());

      return matchSearch && matchAction;
    });
  }, [auditLogs, auditSearch, auditActionFilter]);

  const auditPageSize = 10;
  const totalAuditPages = Math.max(1, Math.ceil(filteredAuditLogs.length / auditPageSize));
  const paginatedAuditLogs = useMemo(() => {
    const start = (auditPage - 1) * auditPageSize;
    return filteredAuditLogs.slice(start, start + auditPageSize);
  }, [filteredAuditLogs, auditPage]);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-3.5 text-textPrimary">
      {/* Header Banner */}
      <div className="flex flex-col gap-3 rounded-2xl border border-borderColor bg-bgCard p-3.5 sm:p-4 backdrop-blur-xl md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accentSubtle text-accentText shrink-0">
            <Settings size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-textPrimary">Enterprise Administration & Settings</h1>
            <p className="text-[11px] text-textMuted">
              Manage platform configuration, user preferences, security policies, and audit trails.
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs Bar */}
      <div role="tablist" aria-label="Settings Navigation" className="flex border-b border-borderMuted gap-1.5 overflow-x-auto">
        {[
          { id: 'profile', label: 'User Profile & Preferences', icon: User },
          { id: 'notifications', label: 'Notification Controls', icon: Bell },
          { id: 'org_branding', label: 'Organization Branding', icon: Palette },
          { id: 'workspace', label: 'Workspace Config', icon: Globe },
          { id: 'security_audit', label: 'Security & Audit Logs', icon: Shield },
        ].map((t) => {
          const Icon = t.icon;
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-label={t.label}
              title={t.label}
              onClick={() => {
                setActiveTab(t.id as any);
                setSuccessMsg(null);
                setErrorMsg(null);
              }}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold border-b-2 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                isActive
                  ? 'border-accent text-accentText bg-accentSubtle'
                  : 'border-transparent text-textMuted hover:text-textPrimary'
              }`}
            >
              <Icon size={14} aria-hidden="true" />
              <span>{t.label}</span>
            </button>
          );
        })}
      </div>

      {/* Global Feedback Banners */}
      {successMsg && (
        <div role="status" aria-live="polite" className="flex items-center gap-2 rounded-xl border border-successBorder bg-successBg p-2.5 text-xs text-successText">
          <Check size={15} aria-hidden="true" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div role="alert" className="flex items-center gap-2 rounded-xl border border-dangerBorder bg-dangerBg p-2.5 text-xs text-dangerText">
          <AlertCircle size={15} aria-hidden="true" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* TAB 1: User Profile & Preferences */}
      {activeTab === 'profile' && (
        <form onSubmit={handleSaveProfile} className="space-y-3.5 max-w-3xl">
          <div className="rounded-2xl border border-borderColor bg-bgCard p-3.5 sm:p-4 space-y-3">
            <h2 className="text-sm font-semibold text-textPrimary flex items-center gap-2">
              <User size={16} className="text-accentText" aria-hidden="true" />
              <span>Personal Information</span>
            </h2>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label htmlFor="settings-username" className="block text-xs font-medium text-textSecondary mb-1">Display Username</label>
                <input
                  id="settings-username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent focus-visible:ring-2 focus-visible:ring-accent"
                />
              </div>

              <div>
                <label htmlFor="settings-email" className="block text-xs font-medium text-textSecondary mb-1">Email Address</label>
                <input
                  id="settings-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent focus-visible:ring-2 focus-visible:ring-accent"
                />
              </div>

              <div>
                <label htmlFor="settings-mobile" className="block text-xs font-medium text-textSecondary mb-1">Mobile Number</label>
                <input
                  id="settings-mobile"
                  type="text"
                  placeholder="+1 (555) 019-2834"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent focus-visible:ring-2 focus-visible:ring-accent"
                />
              </div>

              <div>
                <label htmlFor="settings-avatar" className="block text-xs font-medium text-textSecondary mb-1">Avatar Image URL</label>
                <input
                  id="settings-avatar"
                  type="url"
                  placeholder="https://example.com/avatar.jpg"
                  value={avatarUrl}
                  onChange={(e) => setAvatarUrl(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent focus-visible:ring-2 focus-visible:ring-accent"
                />
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-borderColor bg-bgCard p-6 space-y-4">
            <h3 className="text-sm font-semibold text-textPrimary flex items-center gap-2">
              <Palette size={16} className="text-accentText" />
              <span>Theme & Localization</span>
            </h3>

            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Theme Mode</label>
                <div className="flex gap-2 pt-1">
                  {[
                    { id: 'dark', label: 'Dark', icon: Moon },
                    { id: 'light', label: 'Light', icon: Sun },
                    { id: 'system', label: 'System', icon: Monitor },
                  ].map((item) => {
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setTheme(item.id)}
                        className={`flex-1 flex flex-col items-center gap-1.5 p-2.5 rounded-xl border text-xs font-medium transition-all ${
                          theme === item.id
                            ? 'border-accent bg-accentSubtle text-accentText'
                            : 'border-borderMuted bg-bgTertiary text-textMuted hover:text-textPrimary'
                        }`}
                      >
                        <Icon size={16} />
                        <span>{item.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Language</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                >
                  <option value="en">English (US)</option>
                  <option value="es">Español</option>
                  <option value="fr">Français</option>
                  <option value="de">Deutsch</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Timezone</label>
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                >
                  <option value="UTC">UTC (Universal Coordinated)</option>
                  <option value="America/New_York">America/New_York (EST)</option>
                  <option value="Europe/London">Europe/London (GMT)</option>
                  <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                  <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2 rounded-xl bg-accent px-6 py-2.5 text-xs font-semibold text-white shadow-lg shadow-accent/20 hover:bg-accentHover disabled:opacity-50 transition-all"
            >
              {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              <span>Save Preferences</span>
            </button>
          </div>
        </form>
      )}

      {/* TAB 2: Notification Controls */}
      {activeTab === 'notifications' && (
        <form onSubmit={handleSaveNotifications} className="rounded-2xl border border-borderColor bg-bgCard p-6 max-w-3xl space-y-4">
          <h3 className="text-sm font-semibold text-textPrimary flex items-center gap-2">
            <Bell size={16} className="text-accentText" />
            <span>Notification Preferences</span>
          </h3>

          <div className="divide-y divide-borderMuted">
            <div className="py-3 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-textPrimary">Email Digest & Updates</div>
                <div className="text-[11px] text-textMuted">Receive summary digests and important announcements via email</div>
              </div>
              <input
                type="checkbox"
                checked={emailNotifs}
                onChange={(e) => setEmailNotifs(e.target.checked)}
                className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent cursor-pointer"
              />
            </div>

            <div className="py-3 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-textPrimary">In-App Live Alerts</div>
                <div className="text-[11px] text-textMuted">Display real-time toast notifications while active in MindMesh</div>
              </div>
              <input
                type="checkbox"
                checked={inAppNotifs}
                onChange={(e) => setInAppNotifs(e.target.checked)}
                className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent cursor-pointer"
              />
            </div>

            <div className="py-3 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-textPrimary">Direct Mentions (@user)</div>
                <div className="text-[11px] text-textMuted">Notify immediately when mentioned in messages or document comments</div>
              </div>
              <input
                type="checkbox"
                checked={mentions}
                onChange={(e) => setMentions(e.target.checked)}
                className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent cursor-pointer"
              />
            </div>

            <div className="py-3 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-textPrimary">Project Activity Updates</div>
                <div className="text-[11px] text-textMuted">Receive alerts when milestones or status changes occur in active projects</div>
              </div>
              <input
                type="checkbox"
                checked={projectUpdates}
                onChange={(e) => setProjectUpdates(e.target.checked)}
                className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent cursor-pointer"
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2 rounded-xl bg-accent px-6 py-2.5 text-xs font-semibold text-white shadow-lg shadow-accent/20 hover:bg-accentHover disabled:opacity-50 transition-all"
            >
              {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              <span>Save Notification Controls</span>
            </button>
          </div>
        </form>
      )}

      {/* TAB 3: Organization Branding */}
      {activeTab === 'org_branding' && (
        <form onSubmit={handleSaveOrgBranding} className="space-y-4 max-w-3xl">
          {!canEditOrg && (
            <div className="flex items-center gap-2 rounded-xl border border-infoBorder bg-infoBg p-3 text-xs text-infoText">
              <Info size={16} className="shrink-0" />
              <span>Read-Only View: You need Organization Admin or Owner permission to modify organization branding.</span>
            </div>
          )}

          <div className="rounded-2xl border border-borderColor bg-bgCard p-6 space-y-4">
            <h3 className="text-sm font-semibold text-textPrimary flex items-center gap-2">
              <Palette size={16} className="text-accentText" />
              <span>Organization Branding: {currentOrg?.name}</span>
            </h3>

            {/* Live Branding Preview Card */}
            <div className="rounded-xl border border-borderMuted bg-bgTertiary p-4 space-y-2">
              <div className="text-[11px] font-semibold uppercase text-textMuted">Live Branding Preview</div>
              <div className="flex items-center gap-3">
                <div
                  className="flex h-10 w-10 items-center justify-center rounded-xl font-bold text-white shadow-md overflow-hidden shrink-0"
                  style={{ backgroundColor: orgBrandingColor || '#6366F1' }}
                >
                  {orgLogoUrl ? (
                    <img src={orgLogoUrl} alt="Org Logo" className="h-full w-full object-cover" />
                  ) : (
                    (orgName || currentOrg?.name || 'M').charAt(0).toUpperCase()
                  )}
                </div>
                <div>
                  <div className="text-sm font-bold text-textPrimary">{orgName || currentOrg?.name || 'Organization Name'}</div>
                  <div className="text-[11px] text-textMuted">slug: {currentOrg?.slug} • role: <span className="capitalize text-textPrimary">{currentOrg?.role || 'owner'}</span></div>
                </div>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Organization Name</label>
                <input
                  type="text"
                  required
                  disabled={!canEditOrg}
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent disabled:opacity-60"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Brand Logo URL</label>
                <input
                  type="url"
                  disabled={!canEditOrg}
                  placeholder="https://company.com/logo.png"
                  value={orgLogoUrl}
                  onChange={(e) => setOrgLogoUrl(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent disabled:opacity-60"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Primary Accent Color</label>
                <div className="flex items-center gap-3">
                  <input
                    type="color"
                    disabled={!canEditOrg}
                    value={orgBrandingColor}
                    onChange={(e) => setOrgBrandingColor(e.target.value)}
                    className="h-9 w-14 cursor-pointer rounded-xl border border-borderColor bg-bgInput p-1 outline-none disabled:opacity-60"
                  />
                  <span className="text-xs font-mono text-textPrimary">{orgBrandingColor}</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Company Website</label>
                <input
                  type="text"
                  disabled={!canEditOrg}
                  placeholder="https://acme.com"
                  value={orgWebsite}
                  onChange={(e) => setOrgWebsite(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent disabled:opacity-60"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-textSecondary mb-1">Description</label>
              <textarea
                rows={2}
                disabled={!canEditOrg}
                placeholder="Enterprise organization mission statement or notes..."
                value={orgDescription}
                onChange={(e) => setOrgDescription(e.target.value)}
                className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent disabled:opacity-60"
              />
            </div>
          </div>

          {canEditOrg && (
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center gap-2 rounded-xl bg-accent px-6 py-2.5 text-xs font-semibold text-white shadow-lg shadow-accent/20 hover:bg-accentHover disabled:opacity-50 transition-all"
              >
                {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                <span>Save Organization Branding</span>
              </button>
            </div>
          )}
        </form>
      )}

      {/* TAB 4: Workspace Config */}
      {activeTab === 'workspace' && (
        <form onSubmit={handleSaveWorkspaceConfig} className="space-y-4 max-w-4xl">
          {!canEditWorkspace && (
            <div className="flex items-center gap-2 rounded-xl border border-infoBorder bg-infoBg p-3 text-xs text-infoText">
              <Info size={16} className="shrink-0" />
              <span>Read-Only View: You need Organization Admin or Workspace Owner permission to modify workspace configurations.</span>
            </div>
          )}

          {/* Live Workspace Metrics Bar */}
          <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
            <div className="rounded-2xl border border-borderColor bg-bgCard p-3.5 space-y-1">
              <div className="flex items-center gap-2 text-textMuted text-xs">
                <HardDrive size={14} className="text-accentText" />
                <span>Storage Usage</span>
              </div>
              <div className="text-base font-bold text-textPrimary">{formatBytes(wsStats.storageBytes)}</div>
            </div>

            <div className="rounded-2xl border border-borderColor bg-bgCard p-3.5 space-y-1">
              <div className="flex items-center gap-2 text-textMuted text-xs">
                <Users size={14} className="text-accentText" />
                <span>Members</span>
              </div>
              <div className="text-base font-bold text-textPrimary">{wsStats.memberCount}</div>
            </div>

            <div className="rounded-2xl border border-borderColor bg-bgCard p-3.5 space-y-1">
              <div className="flex items-center gap-2 text-textMuted text-xs">
                <Briefcase size={14} className="text-accentText" />
                <span>Projects</span>
              </div>
              <div className="text-base font-bold text-textPrimary">{wsStats.projectCount}</div>
            </div>

            <div className="rounded-2xl border border-borderColor bg-bgCard p-3.5 space-y-1">
              <div className="flex items-center gap-2 text-textMuted text-xs">
                <FileText size={14} className="text-accentText" />
                <span>Documents</span>
              </div>
              <div className="text-base font-bold text-textPrimary">{wsStats.documentCount}</div>
            </div>
          </div>

          <div className="rounded-2xl border border-borderColor bg-bgCard p-6 space-y-4">
            <h3 className="text-sm font-semibold text-textPrimary flex items-center gap-2">
              <Globe size={16} className="text-accentText" />
              <span>Workspace Details & AI Parameters: {currentWorkspace?.name}</span>
            </h3>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Workspace Name</label>
                <input
                  type="text"
                  required
                  disabled={!canEditWorkspace}
                  value={wsName}
                  onChange={(e) => setWsName(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent disabled:opacity-60"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Workspace Visibility</label>
                <select
                  disabled={!canEditWorkspace}
                  value={wsVisibility}
                  onChange={(e) => setWsVisibility(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent disabled:opacity-60"
                >
                  <option value="private">Private (Workspace Members Only)</option>
                  <option value="team">Team (Organization Shared)</option>
                  <option value="public">Public (Open Enterprise Access)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Default Landing View</label>
                <select
                  disabled={!canEditWorkspace}
                  value={wsDefaultDashboard}
                  onChange={(e) => setWsDefaultDashboard(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent disabled:opacity-60"
                >
                  <option value="dashboard">Dashboard & Intelligence Briefing</option>
                  <option value="projects">Projects Roster</option>
                  <option value="documents">Knowledge Documents Library</option>
                  <option value="messages">Direct Messages & Chat</option>
                  <option value="chat">AI Assistant Chat</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Default AI Grounding Model</label>
                <select
                  disabled={!canEditWorkspace}
                  value={wsDefaultAiModel}
                  onChange={(e) => setWsDefaultAiModel(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent disabled:opacity-60"
                >
                  <option value="gemini-2.5-flash">Gemini 2.5 Flash (Fast & Intelligence)</option>
                  <option value="gemini-2.5-pro">Gemini 2.5 Pro (Deep Reasoning & Analysis)</option>
                  <option value="gpt-4o">OpenAI GPT-4o (Grounded Search)</option>
                  <option value="claude-3-5-sonnet">Claude 3.5 Sonnet (Synthesizer)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Workspace Timezone Override</label>
                <select
                  disabled={!canEditWorkspace}
                  value={wsTimezone}
                  onChange={(e) => setWsTimezone(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent disabled:opacity-60"
                >
                  <option value="UTC">UTC (Universal Coordinated)</option>
                  <option value="America/New_York">America/New_York (EST)</option>
                  <option value="Europe/London">Europe/London (GMT)</option>
                  <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                  <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Default Language</label>
                <select
                  disabled={!canEditWorkspace}
                  value={wsLanguage}
                  onChange={(e) => setWsLanguage(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent disabled:opacity-60"
                >
                  <option value="en">English (US)</option>
                  <option value="es">Español</option>
                  <option value="fr">Français</option>
                  <option value="de">Deutsch</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-textSecondary mb-1">Workspace Description</label>
              <textarea
                rows={2}
                disabled={!canEditWorkspace}
                placeholder="Description of workspace target domain, milestones, and scope..."
                value={wsDescription}
                onChange={(e) => setWsDescription(e.target.value)}
                className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent disabled:opacity-60"
              />
            </div>

            {/* AI Indexing & Features Toggles */}
            <div className="pt-2 border-t border-borderMuted space-y-3">
              <div className="text-xs font-semibold text-textPrimary">Knowledge Intelligence Toggles</div>

              <div className="flex items-center justify-between py-1">
                <div>
                  <div className="text-xs font-semibold text-textPrimary">Auto-Index Uploaded Files</div>
                  <div className="text-[11px] text-textMuted">Automatically generate vector embeddings and OCR parsing on document upload</div>
                </div>
                <input
                  type="checkbox"
                  disabled={!canEditWorkspace}
                  checked={wsAutoIndex}
                  onChange={(e) => setWsAutoIndex(e.target.checked)}
                  className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent cursor-pointer disabled:opacity-60"
                />
              </div>

              <div className="flex items-center justify-between py-1">
                <div>
                  <div className="text-xs font-semibold text-textPrimary">Enable Hybrid Semantic Search</div>
                  <div className="text-[11px] text-textMuted">Permit vector and keyword semantic search across workspace knowledge items</div>
                </div>
                <input
                  type="checkbox"
                  disabled={!canEditWorkspace}
                  checked={wsEnableSemanticSearch}
                  onChange={(e) => setWsEnableSemanticSearch(e.target.checked)}
                  className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent cursor-pointer disabled:opacity-60"
                />
              </div>

              <div className="flex items-center justify-between py-1">
                <div>
                  <div className="text-xs font-semibold text-textPrimary">Enable Grounded AI Chat Assistant</div>
                  <div className="text-[11px] text-textMuted">Allow team members to query AI assistant using workspace context</div>
                </div>
                <input
                  type="checkbox"
                  disabled={!canEditWorkspace}
                  checked={wsEnableAiChat}
                  onChange={(e) => setWsEnableAiChat(e.target.checked)}
                  className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent cursor-pointer disabled:opacity-60"
                />
              </div>
            </div>
          </div>

          {canEditWorkspace && (
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center gap-2 rounded-xl bg-accent px-6 py-2.5 text-xs font-semibold text-white shadow-lg shadow-accent/20 hover:bg-accentHover disabled:opacity-50 transition-all"
              >
                {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                <span>Save Workspace Config</span>
              </button>
            </div>
          )}
        </form>
      )}

      {/* TAB 5: Security & Audit Logs */}
      {activeTab === 'security_audit' && (
        <div className="space-y-6 max-w-4xl">
          {/* Section 1: Security & Access Policies */}
          <form onSubmit={handleSaveSecurity} className="rounded-2xl border border-borderColor bg-bgCard p-6 space-y-4">
            <h3 className="text-sm font-semibold text-textPrimary flex items-center gap-2">
              <Shield size={16} className="text-accentText" />
              <span>Security & Access Policies</span>
            </h3>

            {!canEditOrg && (
              <div className="flex items-center gap-2 rounded-xl border border-infoBorder bg-infoBg p-3 text-xs text-infoText">
                <Info size={16} className="shrink-0" />
                <span>Read-Only View: Only Organization Admins and Owners can modify security policies.</span>
              </div>
            )}

            <div className="space-y-3">
              <div className="flex items-center justify-between rounded-xl border border-borderMuted bg-bgTertiary p-3.5">
                <div>
                  <div className="text-xs font-semibold text-textPrimary">Allow Public Member Invitations</div>
                  <div className="text-[11px] text-textMuted">Permit team members to invite new members to organization</div>
                </div>
                <input
                  type="checkbox"
                  disabled={!canEditOrg}
                  checked={allowPublicInvites}
                  onChange={(e) => setAllowPublicInvites(e.target.checked)}
                  className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent cursor-pointer disabled:opacity-60"
                />
              </div>

              <div className="flex items-center justify-between rounded-xl border border-borderMuted bg-bgTertiary p-3.5">
                <div>
                  <div className="text-xs font-semibold text-textPrimary">Allow Guest Read-Only Access</div>
                  <div className="text-[11px] text-textMuted">Permit external guest users with read-only view access</div>
                </div>
                <input
                  type="checkbox"
                  disabled={!canEditOrg}
                  checked={allowGuestAccess}
                  onChange={(e) => setAllowGuestAccess(e.target.checked)}
                  className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent cursor-pointer disabled:opacity-60"
                />
              </div>
            </div>

            {canEditOrg && (
              <div className="flex justify-end pt-1">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex items-center gap-2 rounded-xl bg-accent px-5 py-2 text-xs font-semibold text-white shadow-lg shadow-accent/20 hover:bg-accentHover disabled:opacity-50 transition-all"
                >
                  {isSubmitting ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
                  <span>Save Security Policies</span>
                </button>
              </div>
            )}
          </form>

          {/* Section 2: Enhanced Audit Log Viewer */}
          <div className="rounded-2xl border border-borderColor bg-bgCard p-6 space-y-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <h3 className="text-sm font-semibold text-textPrimary flex items-center gap-2">
                <Activity size={16} className="text-accentText" />
                <span>Audit Log History ({filteredAuditLogs.length})</span>
              </h3>

              {/* Filters Bar */}
              <div className="flex items-center gap-2 flex-wrap">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-2.5 text-textMuted" />
                  <input
                    type="text"
                    placeholder="Search logs..."
                    value={auditSearch}
                    onChange={(e) => {
                      setAuditSearch(e.target.value);
                      setAuditPage(1);
                    }}
                    className="pl-8 pr-3 py-1.5 rounded-xl border border-borderColor bg-bgInput text-xs text-textPrimary outline-none focus:border-accent w-40 sm:w-48"
                  />
                </div>

                <select
                  value={auditActionFilter}
                  onChange={(e) => {
                    setAuditActionFilter(e.target.value);
                    setAuditPage(1);
                  }}
                  className="rounded-xl border border-borderColor bg-bgInput px-3 py-1.5 text-xs text-textPrimary outline-none focus:border-accent"
                >
                  <option value="all">All Actions</option>
                  <option value="user.profile">Profile Updates</option>
                  <option value="organization">Organization</option>
                  <option value="workspace">Workspace</option>
                  <option value="security">Security</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-textSecondary">
                <thead className="border-b border-borderMuted text-[11px] uppercase tracking-wider text-textMuted">
                  <tr>
                    <th className="pb-3 font-semibold">Action</th>
                    <th className="pb-3 font-semibold">Resource</th>
                    <th className="pb-3 font-semibold">Timestamp</th>
                    <th className="pb-3 font-semibold text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-borderMuted">
                  {paginatedAuditLogs.length > 0 ? (
                    paginatedAuditLogs.map((log) => (
                      <tr
                        key={log.id}
                        onClick={() => setSelectedAuditLog(log)}
                        className="hover:bg-bgHover cursor-pointer transition-colors"
                      >
                        <td className="py-2.5 font-mono text-accentText font-semibold">{log.action}</td>
                        <td className="py-2.5 text-textPrimary">{log.resource_type || 'System'}</td>
                        <td className="py-2.5 text-textMuted">{formatTimestamp(log.created_at, timezone)}</td>
                        <td className="py-2.5 text-right">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedAuditLog(log);
                            }}
                            className="inline-flex items-center gap-1 rounded-lg bg-accentSubtle px-2 py-1 text-[11px] font-semibold text-accentText hover:bg-accent/20 transition-all"
                          >
                            <Eye size={12} />
                            <span>View</span>
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="py-6">
                        <EmptyState
                          title="No matching audit logs"
                          description="Try clearing your search term or action filter."
                          icon={Sliders}
                          variant="compact"
                        />
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {totalAuditPages > 1 && (
              <div className="flex items-center justify-between pt-2 border-t border-borderMuted text-xs text-textMuted">
                <div>
                  Showing {Math.min((auditPage - 1) * auditPageSize + 1, filteredAuditLogs.length)} to {Math.min(auditPage * auditPageSize, filteredAuditLogs.length)} of {filteredAuditLogs.length} events
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    disabled={auditPage === 1}
                    onClick={() => setAuditPage(p => Math.max(1, p - 1))}
                    className="p-1.5 rounded-lg border border-borderColor bg-bgInput hover:bg-bgHover disabled:opacity-40"
                  >
                    <ChevronLeft size={14} />
                  </button>
                  <span className="px-2 font-semibold text-textPrimary">{auditPage} / {totalAuditPages}</span>
                  <button
                    type="button"
                    disabled={auditPage === totalAuditPages}
                    onClick={() => setAuditPage(p => Math.min(totalAuditPages, p + 1))}
                    className="p-1.5 rounded-lg border border-borderColor bg-bgInput hover:bg-bgHover disabled:opacity-40"
                  >
                    <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Audit Log Detail Modal */}
      {selectedAuditLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl border border-borderColor bg-bgCard p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-borderMuted pb-3">
              <div className="flex items-center gap-2">
                <Activity size={18} className="text-accentText" />
                <h3 className="text-sm font-bold text-textPrimary">Audit Event Details</h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedAuditLog(null)}
                className="rounded-lg p-1 text-textMuted hover:bg-bgHover hover:text-textPrimary"
              >
                <X size={16} />
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-textMuted">Action:</span>
                <span className="font-mono font-semibold text-accentText">{selectedAuditLog.action}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-textMuted">Resource Type:</span>
                <span className="font-semibold text-textPrimary">{selectedAuditLog.resource_type || 'System'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-textMuted">User ID:</span>
                <span className="font-mono text-textSecondary">{selectedAuditLog.user_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-textMuted">Timestamp:</span>
                <span className="text-textSecondary">{formatTimestamp(selectedAuditLog.created_at, timezone)}</span>
              </div>

              <div className="pt-2">
                <div className="text-[11px] font-semibold text-textMuted uppercase mb-1">Payload Details</div>
                <pre className="p-3 rounded-xl bg-bgTertiary border border-borderMuted font-mono text-[11px] text-textPrimary overflow-x-auto max-h-48">
                  {JSON.stringify(selectedAuditLog.details || {}, null, 2)}
                </pre>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setSelectedAuditLog(null)}
                className="rounded-xl bg-bgTertiary px-4 py-2 text-xs font-semibold text-textPrimary hover:bg-bgHover"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
