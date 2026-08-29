import React, { useState, useEffect } from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { useAuthStore } from '../../features/auth/auth-store';
import { applyOrganizationAccentColor } from '../../utils/theme';
import * as orgApi from '../../features/auth/api';
import { EmptyState } from '../../shared/components/EmptyState';
import { Building, Shield, Users, Mail, Palette, Globe, Check, Trash2, UserPlus, RefreshCw, AlertCircle, Loader2, Plus, Info } from 'lucide-react';

export const OrganizationSettingsPage: React.FC = () => {
  const { currentOrg, createOrg, token } = useAuth();
  const [activeSubTab, setActiveSubTab] = useState<'general' | 'members' | 'invitations' | 'security'>('general');

  const userRole = (currentOrg?.role || 'member').toLowerCase();
  const canEditOrg = ['owner', 'admin', 'super_admin', 'org_admin'].includes(userRole);

  // Form states
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [website, setWebsite] = useState('');
  const [industry, setIndustry] = useState('');
  const [country, setCountry] = useState('');
  const [timezone, setTimezone] = useState('UTC');
  const [language, setLanguage] = useState('en');
  const [logoUrl, setLogoUrl] = useState('');

  // Settings states
  const [brandingColor, setBrandingColor] = useState('#3B82F6');
  const [allowPublicInvites, setAllowPublicInvites] = useState(false);
  const [allowGuestAccess, setAllowGuestAccess] = useState(true);

  // Members & Invites
  const [members, setMembers] = useState<any[]>([]);
  const [invitations, setInvitations] = useState<any[]>([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');

  // Status
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (currentOrg) {
      setName(currentOrg.name || '');
      setDescription(currentOrg.description || '');
      setWebsite(currentOrg.website || '');
      setIndustry(currentOrg.industry || '');
      setCountry(currentOrg.country || '');
      setTimezone(currentOrg.timezone || 'UTC');
      setLanguage(currentOrg.language || 'en');
      setLogoUrl(currentOrg.logo_url || '');

      loadOrgDetails();
    }
  }, [currentOrg?.id]);

  const loadOrgDetails = async () => {
    if (!currentOrg) return;
    setLoading(true);
    try {
      const [membersData, invitesData, settingsData] = await Promise.all([
        orgApi.getOrgMembers(currentOrg.id).catch(() => []),
        orgApi.getOrgInvitations(currentOrg.id).catch(() => []),
        orgApi.getOrgSettings(currentOrg.id).catch(() => null)
      ]);
      setMembers(membersData);
      setInvitations(invitesData);
      if (settingsData) {
        const color = settingsData.branding_color || '#3B82F6';
        setBrandingColor(color);
        applyOrganizationAccentColor(color);
        setAllowPublicInvites(settingsData.allow_public_invites ?? false);
        setAllowGuestAccess(settingsData.allow_guest_access ?? true);
      }
    } catch (err: any) {
      console.error("Failed to load org details:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveGeneral = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg) return;
    setSaving(true);
    setMessage(null);
    try {
      const [updatedOrg, updatedSettings] = await Promise.all([
        orgApi.updateOrganization(currentOrg.id, {
          name,
          description,
          website,
          industry,
          country,
          timezone,
          language,
          logo_url: logoUrl
        }),
        orgApi.updateOrgSettings(currentOrg.id, {
          branding_color: brandingColor,
          allow_public_invites: allowPublicInvites,
          allow_guest_access: allowGuestAccess
        })
      ]);

      applyOrganizationAccentColor(brandingColor);

      if (updatedOrg) {
        const store = useAuthStore.getState();
        const mergedOrg = {
          ...currentOrg,
          ...updatedOrg,
          settings: {
            ...(currentOrg.settings || {}),
            ...(updatedSettings || {}),
            branding_color: brandingColor
          }
        };
        store.setCurrentOrg(mergedOrg as any);
        const refreshedOrgs = store.organizations.map(o => o.id === mergedOrg.id ? mergedOrg : o);
        store.setOrganizations(refreshedOrgs as any);
      }

      await loadOrgDetails();
      setMessage({ type: 'success', text: 'Organization details updated successfully!' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to update organization' });
    } finally {
      setSaving(false);
    }
  };

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg) return;
    setSaving(true);
    setMessage(null);
    try {
      await orgApi.updateOrgSettings(currentOrg.id, {
        branding_color: brandingColor,
        allow_public_invites: allowPublicInvites,
        allow_guest_access: allowGuestAccess
      });
      setMessage({ type: 'success', text: 'Organization settings updated successfully!' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to update settings' });
    } finally {
      setSaving(false);
    }
  };

  const handleSendInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg || !inviteEmail.trim()) return;
    const emailSentTo = inviteEmail.trim();
    setSaving(true);
    setMessage(null);
    try {
      await orgApi.inviteOrgMember(currentOrg.id, emailSentTo, inviteRole);
      setInviteEmail('');
      await loadOrgDetails();
      setMessage({ type: 'success', text: `Invitation sent to ${emailSentTo}` });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to send invitation' });
    } finally {
      setSaving(false);
    }
  };

  const handleRoleChange = async (memberUserId: string, newRole: string) => {
    if (!currentOrg) return;
    try {
      await orgApi.updateOrgMemberRole(currentOrg.id, memberUserId, newRole);
      await loadOrgDetails();
      setMessage({ type: 'success', text: 'Member role updated' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to update role' });
    }
  };

  const handleRemoveMember = async (memberUserId: string) => {
    if (!currentOrg || !window.confirm("Are you sure you want to remove this member?")) return;
    try {
      await orgApi.removeOrgMember(currentOrg.id, memberUserId);
      await loadOrgDetails();
      setMessage({ type: 'success', text: 'Member removed from organization' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Failed to remove member' });
    }
  };

  if (!currentOrg) {
    return (
      <EmptyState
        title="No organizations available"
        description="Create an organization to start collaborating with your team."
        icon={Building}
        variant="page"
        primaryAction={{
          label: "Create Organization",
          onClick: async () => {
            const orgName = prompt("Enter new organization name:");
            if (orgName) {
              const slug = orgName.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
              try {
                await createOrg(orgName, slug);
              } catch (e: any) {
                alert(e.message || "Failed to create organization");
              }
            }
          },
          icon: Plus
        }}
      />
    );
  }

  return (
    <div className="space-y-3.5 text-textPrimary">
      {/* Header Banner */}
      <div className="flex flex-col gap-3 rounded-2xl border border-borderColor bg-bgCard p-3.5 sm:p-4 backdrop-blur-xl md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent text-base font-bold text-white shadow-lg shrink-0"
            style={{ backgroundColor: brandingColor }}
          >
            {logoUrl ? (
              <img src={logoUrl} alt={name} className="h-full w-full rounded-xl object-cover" />
            ) : (
              name.charAt(0).toUpperCase()
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-textPrimary">{name}</h1>
              {currentOrg.is_personal && (
                <span className="rounded-full bg-accentSubtle px-2 py-0.2 text-[10px] font-semibold text-accentText">
                  Personal Org
                </span>
              )}
            </div>
            <p className="text-[11px] text-textMuted">slug: {currentOrg.slug} • role: <span className="capitalize text-textPrimary">{currentOrg.role || 'owner'}</span></p>
          </div>
        </div>
      </div>

      {/* Sub Tabs */}
      <div className="flex border-b border-borderMuted gap-1.5 overflow-x-auto">
        {[
          { id: 'general', label: 'General', icon: Building },
          { id: 'members', label: `Members (${members.length})`, icon: Users },
          { id: 'invitations', label: `Invitations (${invitations.length})`, icon: Mail },
          { id: 'security', label: 'Security & Access', icon: Shield },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeSubTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id as any)}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold border-b-2 transition-all ${
                isActive
                  ? 'border-accent text-accentText bg-accentSubtle'
                  : 'border-transparent text-textMuted hover:text-textPrimary'
              }`}
            >
              <Icon size={13} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {!canEditOrg && (
        <div className="flex items-center gap-2 rounded-xl border border-infoBorder bg-infoBg p-3 text-xs text-infoText">
          <Info size={16} className="shrink-0" />
          <span>Read-Only View: You are currently logged in with {userRole} role. Only Organization Admins and Owners can modify organization settings or policies.</span>
        </div>
      )}

      {/* Feedback Banner */}
      {message && (
        <div className={`flex items-center gap-2 rounded-xl border p-2.5 text-xs ${
          message.type === 'success'
            ? 'border-successBorder bg-successBg text-successText'
            : 'border-dangerBorder bg-dangerBg text-dangerText'
        }`}>
          <AlertCircle size={14} />
          <span>{message.text}</span>
        </div>
      )}

      {/* Tab 1: General Info */}
      {activeSubTab === 'general' && (
        <form onSubmit={handleSaveGeneral} className="rounded-2xl border border-borderColor bg-bgCard p-3.5 sm:p-4 space-y-4">
          <div className="space-y-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-textMuted">General Information</h2>

            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="block text-xs font-medium text-textMuted mb-1">Organization Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-1.5 text-xs text-textPrimary outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-textMuted mb-1">Website URL</label>
                <input
                  type="text"
                  placeholder="https://acme.com"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3.5 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-textMuted mb-1">Industry</label>
                <input
                  type="text"
                  placeholder="Technology, Finance, Healthcare..."
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3.5 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-textMuted mb-1">Country</label>
                <input
                  type="text"
                  placeholder="United States, India, Germany..."
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3.5 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-textMuted mb-1">Description</label>
              <textarea
                rows={3}
                placeholder="Provide a brief summary of your organization's mission and team structure."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full rounded-xl border border-borderColor bg-bgInput px-3.5 py-2 text-xs text-textPrimary outline-none focus:border-accent"
              />
            </div>
          </div>

          <hr className="border-borderMuted my-2" />

          {/* Subsection: Branding & Identity */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Palette size={14} className="text-accent" />
              <h2 className="text-xs font-bold uppercase tracking-wider text-textMuted">Branding & Identity</h2>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div>
                <label className="block text-xs font-medium text-textMuted mb-1">Logo URL</label>
                <input
                  type="text"
                  placeholder="https://example.com/logo.png"
                  value={logoUrl}
                  onChange={(e) => setLogoUrl(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3.5 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-textMuted mb-1">Organization Logo Upload</label>
                <div className="flex items-center gap-3">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        const reader = new FileReader();
                        reader.onload = (event) => {
                          if (event.target?.result) {
                            setLogoUrl(event.target.result as string);
                          }
                        };
                        reader.readAsDataURL(file);
                      }
                    }}
                    className="w-full text-xs text-textMuted file:mr-3 file:py-1.5 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-accentSubtle file:text-accentText hover:file:bg-accent/20 cursor-pointer"
                  />
                  {logoUrl && (
                    <div className="h-9 w-9 shrink-0 overflow-hidden rounded-xl border border-borderColor bg-bgTertiary p-0.5">
                      <img src={logoUrl} alt="Logo Preview" className="h-full w-full object-cover rounded-lg" />
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-textMuted mb-2">Accent Color Picker</label>
              <div className="flex items-center gap-3">
                <input
                  type="color"
                  value={brandingColor}
                  onChange={(e) => {
                    const newColor = e.target.value;
                    setBrandingColor(newColor);
                    applyOrganizationAccentColor(newColor);
                  }}
                  className="h-9 w-12 cursor-pointer rounded-lg border border-borderColor bg-bgInput p-1"
                />
                <span className="text-xs font-mono text-textSecondary">{brandingColor}</span>
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-1.5 rounded-xl bg-accent px-5 py-2 text-xs font-semibold text-white hover:bg-accentHover transition-all disabled:opacity-50"
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
              <span>Save Changes</span>
            </button>
          </div>
        </form>
      )}

      {/* Tab 3: Members & Roles */}
      {activeSubTab === 'members' && (
        <div className="rounded-2xl border border-borderColor bg-bgCard p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-textPrimary">Organization Members ({members.length})</h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-textSecondary">
              <thead className="border-b border-borderMuted text-[11px] uppercase tracking-wider text-textMuted">
                <tr>
                  <th className="pb-3 font-semibold">User</th>
                  <th className="pb-3 font-semibold">Role</th>
                  <th className="pb-3 font-semibold">Joined</th>
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borderMuted">
                {members.map((m) => (
                  <tr key={m.user_id} className="hover:bg-bgHover transition-colors">
                    <td className="py-3">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-bgTertiary font-bold text-textSecondary">
                          {m.username?.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-semibold text-textPrimary">{m.username}</div>
                          <div className="text-[11px] text-textMuted">{m.email}</div>
                        </div>
                      </div>
                    </td>

                    <td className="py-3">
                      <select
                        value={m.role}
                        onChange={(e) => handleRoleChange(m.user_id, e.target.value)}
                        className="rounded-lg border border-borderColor bg-bgInput px-2 py-1 text-xs text-textPrimary outline-none focus:border-accent capitalize"
                      >
                        <option value="owner">Owner</option>
                        <option value="admin">Admin</option>
                        <option value="manager">Manager</option>
                        <option value="member">Member</option>
                        <option value="guest">Guest</option>
                      </select>
                    </td>

                    <td className="py-3 text-textMuted">
                      {new Date(m.joined_at).toLocaleDateString()}
                    </td>

                    <td className="py-3 text-right">
                      <button
                        onClick={() => handleRemoveMember(m.user_id)}
                        className="rounded-lg border border-dangerBorder bg-dangerBg p-1.5 text-dangerText hover:bg-red-600 hover:text-white transition-all"
                        title="Remove member"
                      >
                        <Trash2 size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Invitations */}
      {activeSubTab === 'invitations' && (
        <div className="space-y-6">
          {/* Invite Form */}
          <form onSubmit={handleSendInvite} className="rounded-2xl border border-borderColor bg-bgCard p-6 space-y-4">
            <h2 className="text-sm font-bold text-textPrimary">Invite Team Member</h2>
            <div className="flex flex-col gap-3 md:flex-row md:items-center">
              <input
                type="email"
                required
                placeholder="colleague@company.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                className="flex-1 rounded-xl border border-borderColor bg-bgInput px-3.5 py-2 text-xs text-textPrimary outline-none focus:border-accent"
              />
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                className="rounded-xl border border-borderColor bg-bgInput px-3.5 py-2 text-xs text-textPrimary outline-none focus:border-accent capitalize"
              >
                <option value="admin">Admin</option>
                <option value="manager">Manager</option>
                <option value="member">Member</option>
                <option value="guest">Guest</option>
              </select>
              <button
                type="submit"
                disabled={saving}
                className="flex items-center gap-1.5 rounded-xl bg-accent px-5 py-2 text-xs font-semibold text-white hover:bg-accentHover transition-all disabled:opacity-50"
              >
                <UserPlus size={14} />
                <span>Send Invitation</span>
              </button>
            </div>
          </form>

          {/* Pending Invitations Table */}
          <div className="rounded-2xl border border-borderColor bg-bgCard p-6 space-y-4">
            <h2 className="text-sm font-bold text-textPrimary">Pending Invitations ({invitations.length})</h2>
            {invitations.length === 0 ? (
              <p className="text-xs text-textMuted">No active pending invitations.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-textSecondary">
                  <thead className="border-b border-borderMuted text-[11px] uppercase tracking-wider text-textMuted">
                    <tr>
                      <th className="pb-3 font-semibold">Email</th>
                      <th className="pb-3 font-semibold">Role</th>
                      <th className="pb-3 font-semibold">Status</th>
                      <th className="pb-3 font-semibold">Expires</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-borderMuted">
                    {invitations.map((inv) => (
                      <tr key={inv.id}>
                        <td className="py-3 font-medium text-textPrimary">{inv.email}</td>
                        <td className="py-3 capitalize text-textSecondary">{inv.role}</td>
                        <td className="py-3">
                          <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-500 uppercase">
                            {inv.status}
                          </span>
                        </td>
                        <td className="py-3 text-textMuted">{new Date(inv.expires_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 5: Security */}
      {activeSubTab === 'security' && (
        <form onSubmit={handleSaveSettings} className="rounded-2xl border border-borderColor bg-bgCard p-6 space-y-4">
          <h2 className="text-sm font-bold text-textPrimary">Security & Access Policies</h2>

          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-xl border border-borderMuted bg-bgTertiary p-4">
              <div>
                <div className="text-xs font-semibold text-textPrimary">Allow Public Invitations</div>
                <div className="text-[11px] text-textMuted">Permit members to share invitation links publicly</div>
              </div>
              <input
                type="checkbox"
                checked={allowPublicInvites}
                onChange={(e) => setAllowPublicInvites(e.target.checked)}
                className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent"
              />
            </div>

            <div className="flex items-center justify-between rounded-xl border border-borderMuted bg-bgTertiary p-4">
              <div>
                <div className="text-xs font-semibold text-textPrimary">Allow Guest Access</div>
                <div className="text-[11px] text-textMuted">Permit read-only guest users to access workspaces</div>
              </div>
              <input
                type="checkbox"
                checked={allowGuestAccess}
                onChange={(e) => setAllowGuestAccess(e.target.checked)}
                className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent"
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-1.5 rounded-xl bg-accent px-5 py-2 text-xs font-semibold text-white hover:bg-accentHover transition-all disabled:opacity-50"
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
              <span>Save Security Policies</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
