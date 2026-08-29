import React, { useState, useEffect } from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { useWorkspaceStore } from '../../features/workspace/store';
import { useProjectStore } from '../../features/projects/store';
import { useMemberStore } from '../../features/members/store';
import {
  Users, Search, UserPlus, Shield, Mail, CheckCircle2, XCircle, Clock,
  MoreVertical, Copy, Trash2, ArrowUpRight, Crown, AlertTriangle, Key, Filter, Check, X, Loader2
} from 'lucide-react';

const ROLE_BADGES: Record<string, { bg: string; text: string }> = {
  owner: { bg: 'bg-amber-500/10 border-amber-500/30', text: 'text-amber-400' },
  admin: { bg: 'bg-purple-500/10 border-purple-500/30', text: 'text-purple-400' },
  manager: { bg: 'bg-indigo-500/10 border-indigo-500/30', text: 'text-indigo-400' },
  contributor: { bg: 'bg-blue-500/10 border-blue-500/30', text: 'text-blue-400' },
  member: { bg: 'bg-emerald-500/10 border-emerald-500/30', text: 'text-emerald-400' },
  guest: { bg: 'bg-slate-500/10 border-slate-500/30', text: 'text-slate-400' },
  viewer: { bg: 'bg-slate-500/10 border-slate-500/30', text: 'text-slate-400' },
};

export const MembersPage: React.FC = () => {
  const { token, currentOrg, user: currentUser } = useAuth();
  const { currentWorkspace, workspaces } = useWorkspaceStore();
  const { projects } = useProjectStore();
  const {
    members, invitations, joinRequests, permissionMatrix, loading,
    fetchDirectory, fetchInvitations, fetchJoinRequests, fetchPermissionMatrix,
    issueInvitation, cancelInvitation, approveJoinRequest, rejectJoinRequest,
    updateMemberAction, removeMember
  } = useMemberStore();

  const [activeTab, setActiveTab] = useState<'directory' | 'invitations' | 'join_requests' | 'matrix'>('directory');
  
  // Filters
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string>('');
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');

  // Modal State
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [inviteScope, setInviteScope] = useState<'org' | 'workspace' | 'project'>('org');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  useEffect(() => {
    if (token && currentOrg) {
      fetchDirectory(
        token, currentOrg.id,
        selectedWorkspaceId || undefined,
        selectedProjectId || undefined,
        searchQuery || undefined,
        roleFilter === 'all' ? undefined : roleFilter
      );
      fetchInvitations(token, currentOrg.id);
      fetchJoinRequests(token, currentOrg.id);
      fetchPermissionMatrix(token, currentOrg.id);
    }
  }, [token, currentOrg, selectedWorkspaceId, selectedProjectId, searchQuery, roleFilter]);

  const handleIssueInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !currentOrg || !inviteEmail.trim()) return;
    const cleanEmail = inviteEmail.trim();
    setIsSubmitting(true);
    try {
      await issueInvitation(token, currentOrg.id, {
        organization_id: currentOrg.id,
        workspace_id: inviteScope !== 'org' ? (selectedWorkspaceId || currentWorkspace?.id) : undefined,
        project_id: inviteScope === 'project' ? selectedProjectId : undefined,
        email: cleanEmail,
        role: inviteRole,
      });
      setInviteEmail('');
      setShowInviteModal(false);
      await fetchInvitations(token, currentOrg.id);
    } catch (err: any) {
      alert(err.message || 'Failed to send invitation');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRoleChange = async (userId: string, newRole: string) => {
    if (!token || !currentOrg) return;
    try {
      await updateMemberAction(token, currentOrg.id, userId, {
        level: 'organization',
        role: newRole
      });
    } catch (err: any) {
      alert(err.message || 'Failed to update member role');
    }
  };

  const handleTransferOwnership = async (targetUserId: string, targetUsername: string) => {
    if (!token || !currentOrg || !confirm(`Are you sure you want to transfer Organization Ownership to ${targetUsername}? You will become an Admin.`)) return;
    try {
      await updateMemberAction(token, currentOrg.id, targetUserId, {
        action: 'transfer_ownership',
        level: 'organization'
      });
    } catch (err: any) {
      alert(err.message || 'Failed to transfer ownership');
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!token || !currentOrg || !confirm("Remove member from organization?")) return;
    try {
      await removeMember(token, currentOrg.id, userId, 'organization');
    } catch (err: any) {
      alert(err.message || 'Failed to remove member');
    }
  };

  const copyInviteLink = (tokenStr: string) => {
    const link = `${window.location.origin}/invite/${tokenStr}`;
    navigator.clipboard.writeText(link);
    setCopiedToken(tokenStr);
    setTimeout(() => setCopiedToken(null), 2000);
  };

  return (
    <div className="space-y-3.5">
      {/* Header Banner */}
      <div className="flex flex-col gap-3 rounded-2xl border border-borderColor bg-bgCard p-3.5 sm:p-4 backdrop-blur-xl md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accentSubtle text-accentText shrink-0" aria-hidden="true">
            <Users size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-textPrimary">Member & Collaboration Directory</h1>
            <p className="text-[11px] text-textMuted">
              Manage enterprise access, roles, invitations, and join requests across <span className="font-semibold text-textSecondary">{currentOrg?.name || 'Organization'}</span>
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setShowInviteModal(true)}
          aria-label="Invite Teammate"
          title="Invite Teammate"
          className="flex items-center gap-1.5 rounded-xl bg-accent px-3 py-1.5 text-xs font-semibold text-white shadow-lg shadow-accent/20 hover:bg-accentHover transition-all shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          <UserPlus size={14} aria-hidden="true" />
          <span>Invite Teammate</span>
        </button>
      </div>

      {/* Sub Tabs & Filters */}
      <div className="flex flex-col gap-3 border-b border-borderMuted pb-2 md:flex-row md:items-center md:justify-between">
        <div role="tablist" aria-label="Directory Navigation" className="flex items-center gap-1.5 overflow-x-auto">
          {[
            { id: 'directory', label: `Directory (${members.length})`, icon: Users },
            { id: 'invitations', label: `Invitations (${invitations.length})`, icon: Mail },
            { id: 'join_requests', label: `Join Requests (${joinRequests.length})`, icon: Clock },
            { id: 'matrix', label: 'Permission Matrix', icon: Key },
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
                onClick={() => setActiveTab(t.id as any)}
                className={`flex items-center gap-1.5 rounded-xl px-2.5 py-1.5 text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                  isActive
                    ? 'bg-accent text-white shadow-md'
                    : 'text-textMuted hover:bg-bgHover hover:text-textPrimary'
                }`}
              >
                <Icon size={13} aria-hidden="true" />
                <span>{t.label}</span>
              </button>
            );
          })}
        </div>

        {/* Filters */}
        {activeTab === 'directory' && (
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={selectedWorkspaceId}
              onChange={(e) => setSelectedWorkspaceId(e.target.value)}
              aria-label="Filter by workspace"
              title="Filter by workspace"
              className="rounded-xl border border-borderColor bg-bgInput px-2.5 py-1 text-xs text-textPrimary outline-none focus:border-accent focus-visible:ring-2 focus-visible:ring-accent"
            >
              <option value="">All Workspaces</option>
              {workspaces.map((w) => (
                <option key={w.id} value={w.id}>{w.name}</option>
              ))}
            </select>

            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              aria-label="Filter by role"
              title="Filter by role"
              className="rounded-xl border border-borderColor bg-bgInput px-2.5 py-1 text-xs text-textPrimary outline-none focus:border-accent capitalize focus-visible:ring-2 focus-visible:ring-accent"
            >
              <option value="all">All Roles</option>
              {['owner', 'admin', 'manager', 'contributor', 'member', 'guest', 'viewer'].map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>

            <div className="relative">
              <Search className="absolute left-3 top-1.5 h-3.5 w-3.5 text-textMuted" />
              <input
                type="text"
                placeholder="Search directory..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-44 rounded-xl border border-borderColor bg-bgInput py-1 pl-8 pr-3 text-xs text-textPrimary placeholder-textMuted outline-none focus:border-accent"
              />
            </div>
          </div>
        )}
      </div>

      {/* Tab 1: User Directory Roster */}
      {activeTab === 'directory' && (
        <div className="rounded-2xl border border-borderColor bg-bgCard p-4 backdrop-blur-md">
          {loading ? (
            <div className="py-12 text-center text-textMuted">
              <Loader2 className="mx-auto mb-2 h-6 w-6 animate-spin text-accentText" />
              Loading member directory...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-textSecondary">
                <thead className="border-b border-borderMuted text-[11px] uppercase tracking-wider text-textMuted">
                  <tr>
                    <th className="pb-3 font-semibold">User</th>
                    <th className="pb-3 font-semibold">Organization Role</th>
                    <th className="pb-3 font-semibold">Status</th>
                    <th className="pb-3 font-semibold">Last Active</th>
                    <th className="pb-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-borderMuted">
                  {members.map((m) => {
                    const badge = ROLE_BADGES[m.org_role || 'member'] || ROLE_BADGES.member;
                    const isSelf = m.user_id === currentUser?.id;

                    return (
                      <tr key={m.user_id} className="hover:bg-bgHover transition-colors">
                        <td className="py-3">
                          <div className="flex items-center gap-3">
                            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accentSubtle font-bold text-accentText uppercase border border-accent/20">
                              {m.username.charAt(0)}
                            </div>
                            <div>
                              <div className="font-semibold text-textPrimary flex items-center gap-1.5">
                                <span>{m.username}</span>
                                {m.org_role === 'owner' && <Crown size={13} className="text-amber-400" />}
                                {isSelf && <span className="text-[10px] text-accentText bg-accentSubtle px-1.5 py-0.2 rounded">(You)</span>}
                              </div>
                              <div className="text-[11px] text-textMuted">{m.email}</div>
                            </div>
                          </div>
                        </td>

                        <td className="py-3">
                          <select
                            value={m.org_role || 'member'}
                            disabled={m.org_role === 'owner' || isSelf}
                            onChange={(e) => handleRoleChange(m.user_id, e.target.value)}
                            className={`rounded-lg border px-2.5 py-1 text-xs font-semibold capitalize bg-bgInput ${badge.bg} ${badge.text}`}
                          >
                            {['owner', 'admin', 'manager', 'contributor', 'member', 'guest', 'viewer'].map((r) => (
                              <option key={r} value={r}>{r}</option>
                            ))}
                          </select>
                        </td>

                        <td className="py-3">
                          <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                            m.status === 'active' ? 'bg-successBg text-successText' : 'bg-dangerBg text-dangerText'
                          }`}>
                            <span className={`h-1.5 w-1.5 rounded-full ${m.status === 'active' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                            <span className="capitalize">{m.status}</span>
                          </span>
                        </td>

                        <td className="py-3 text-textMuted text-[11px]">
                          {m.last_login_at ? new Date(m.last_login_at).toLocaleDateString() : 'Recently'}
                        </td>

                        <td className="py-3 text-right">
                          <div className="flex items-center justify-end gap-1">
                            {m.org_role !== 'owner' && (
                              <button
                                onClick={() => handleTransferOwnership(m.user_id, m.username)}
                                className="rounded-lg p-1.5 text-textMuted hover:text-amber-400 transition-colors"
                                title="Transfer Ownership"
                              >
                                <Crown size={14} />
                              </button>
                            )}

                            {!isSelf && m.org_role !== 'owner' && (
                              <button
                                onClick={() => handleRemoveMember(m.user_id)}
                                className="rounded-lg p-1.5 text-textMuted hover:text-red-400 transition-colors"
                                title="Remove Member"
                              >
                                <Trash2 size={14} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Invitations & Links */}
      {activeTab === 'invitations' && (
        <div className="rounded-2xl border border-borderColor bg-bgCard p-4 backdrop-blur-md space-y-4">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-textSecondary">
              <thead className="border-b border-borderMuted text-[11px] uppercase tracking-wider text-textMuted">
                <tr>
                  <th className="pb-3 font-semibold">Invitee Email</th>
                  <th className="pb-3 font-semibold">Role</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Expires</th>
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borderMuted">
                {invitations.map((inv) => (
                  <tr key={inv.id}>
                    <td className="py-3 font-semibold text-textPrimary">{inv.email}</td>
                    <td className="py-3 capitalize text-accentText">{inv.role}</td>
                    <td className="py-3">
                      <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold text-amber-500 border border-amber-500/30">
                        {inv.status}
                      </span>
                    </td>
                    <td className="py-3 text-textMuted">{new Date(inv.expires_at).toLocaleDateString()}</td>
                    <td className="py-3 text-right flex items-center justify-end gap-2">
                      <button
                        onClick={() => copyInviteLink(inv.token)}
                        className="flex items-center gap-1 rounded-lg bg-bgTertiary px-2.5 py-1 text-[11px] text-textSecondary hover:text-textPrimary border border-borderMuted"
                      >
                        <Copy size={12} />
                        <span>{copiedToken === inv.token ? 'Copied Link!' : 'Copy Link'}</span>
                      </button>
                      <button
                        onClick={() => cancelInvitation(token!, currentOrg!.id, inv.id)}
                        className="text-dangerText hover:underline p-1"
                        title="Cancel Invitation"
                      >
                        <X size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Join Requests */}
      {activeTab === 'join_requests' && (
        <div className="rounded-2xl border border-borderColor bg-bgCard p-4 backdrop-blur-md">
          {joinRequests.length === 0 ? (
            <div className="py-12 text-center text-textMuted">No pending join requests.</div>
          ) : (
            <div className="space-y-3">
              {joinRequests.map((req) => (
                <div key={req.id} className="flex items-center justify-between rounded-xl border border-borderMuted bg-bgTertiary p-3.5">
                  <div>
                    <div className="font-semibold text-textPrimary text-xs">{req.username || req.email}</div>
                    <div className="text-[11px] text-textMuted">{req.message || 'Requested membership access.'}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => approveJoinRequest(token!, currentOrg!.id, req.id)}
                      className="flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
                    >
                      <Check size={14} /> Approve
                    </button>
                    <button
                      onClick={() => rejectJoinRequest(token!, currentOrg!.id, req.id)}
                      className="flex items-center gap-1 rounded-lg bg-bgCard px-3 py-1.5 text-xs font-semibold text-textMuted hover:bg-bgHover border border-borderMuted"
                    >
                      <X size={14} /> Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Permission Matrix */}
      {activeTab === 'matrix' && (
        <div className="rounded-2xl border border-borderColor bg-bgCard p-4 backdrop-blur-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-textSecondary">
              <thead className="border-b border-borderMuted text-[11px] uppercase tracking-wider text-textMuted">
                <tr>
                  <th className="pb-3 font-semibold">Role</th>
                  <th className="pb-3 font-semibold">Permission Key</th>
                  <th className="pb-3 font-semibold">Granted</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borderMuted">
                {permissionMatrix.map((item, idx) => (
                  <tr key={idx}>
                    <td className="py-2.5 font-semibold text-textPrimary capitalize">{item.role_name}</td>
                    <td className="py-2.5 font-mono text-accentText">{item.permission_key}</td>
                    <td className="py-2.5">
                      <span className="inline-flex items-center gap-1 text-successText">
                        <CheckCircle2 size={14} /> Granted
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Issue Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-bgOverlay backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-2xl border border-borderColor bg-bgDialog p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-borderMuted pb-3">
              <div className="flex items-center gap-2">
                <UserPlus size={18} className="text-accentText" />
                <h3 className="text-base font-semibold text-textPrimary">Invite Teammate</h3>
              </div>
              <button onClick={() => setShowInviteModal(false)} className="text-textMuted hover:text-textPrimary">
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleIssueInvite} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Teammate Email</label>
                <input
                  type="email"
                  required
                  placeholder="colleague@company.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Assign Role</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none capitalize"
                >
                  <option value="owner">Owner</option>
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="contributor">Contributor</option>
                  <option value="member">Member</option>
                  <option value="guest">Guest</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="rounded-xl border border-borderColor px-4 py-2 text-xs text-textMuted hover:bg-bgHover hover:text-textPrimary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex items-center gap-1.5 rounded-xl bg-accent px-4 py-2 text-xs font-semibold text-white hover:bg-accentHover disabled:opacity-50"
                >
                  {isSubmitting ? <Loader2 size={14} className="animate-spin" /> : 'Send Invitation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default MembersPage;
