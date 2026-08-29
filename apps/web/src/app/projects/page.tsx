import React, { useState, useEffect } from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { useWorkspaceStore } from '../../features/workspace/store';
import { useProjectStore, Project } from '../../features/projects/store';
import * as projectApi from '../../features/projects/api';
import { EmptyState } from '../../shared/components/EmptyState';
import {
  Briefcase, Search, Plus, Calendar, Users, Layers, Shield, Settings, Archive,
  RotateCcw, Trash2, ChevronRight, CheckCircle2, Clock, AlertCircle, FileText,
  MessageSquare, CheckSquare, Loader2, Sparkles, Filter, MoreVertical, X
} from 'lucide-react';

const STATUS_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  planning: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30' },
  active: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  on_hold: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30' },
  completed: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30' },
  archived: { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/30' },
  cancelled: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30' },
};

const PROJECT_COLORS = ['#3B82F6', '#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#EF4444', '#06B6D4'];

export const ProjectsPage: React.FC = () => {
  const { token, currentOrg } = useAuth();
  const { currentWorkspace, workspaces } = useWorkspaceStore();
  const { projects, fetchProjects, createProject, updateProject, archiveProject, restoreProject, deleteProject, loading } = useProjectStore();

  // Filter States
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Modals & Active Detail Views
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [viewingDashboard, setViewingDashboard] = useState<Project | null>(null);

  // Create/Edit Form State
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [color, setColor] = useState('#3B82F6');
  const [visibility, setVisibility] = useState('private');
  const [statusVal, setStatusVal] = useState('active');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Dashboard Detail Drawer Tab State
  const [dashboardTab, setDashboardTab] = useState<'overview' | 'members' | 'settings'>('overview');
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [members, setMembers] = useState<any[]>([]);
  const [projectSettings, setProjectSettings] = useState<any>(null);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('contributor');
  const [dashLoading, setDashLoading] = useState(false);

  useEffect(() => {
    if (token && currentOrg) {
      fetchProjects(
        token,
        currentOrg.id,
        selectedWorkspaceId || undefined,
        statusFilter === 'all' ? undefined : statusFilter,
        searchQuery || undefined
      );
    }
  }, [token, currentOrg, selectedWorkspaceId, statusFilter, searchQuery, fetchProjects]);

  useEffect(() => {
    if (currentWorkspace) {
      setSelectedWorkspaceId(currentWorkspace.id);
    }
  }, [currentWorkspace]);

  const handleNameChange = (val: string) => {
    setName(val);
    if (!slug) {
      setSlug(val.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, ''));
    }
  };

  const handleSaveProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !token || !currentOrg) return;
    const wsId = selectedWorkspaceId || currentWorkspace?.id || (workspaces[0] && workspaces[0].id);
    if (!wsId) {
      setFormError("Please select a workspace for this project.");
      return;
    }

    setIsSubmitting(true);
    setFormError(null);
    try {
      if (editingProject) {
        await updateProject(token, currentOrg.id, editingProject.id, {
          name,
          slug,
          description,
          color,
          visibility,
          status: statusVal,
          start_date: startDate ? new Date(startDate).toISOString() : null,
          end_date: endDate ? new Date(endDate).toISOString() : null,
        });
        setEditingProject(null);
      } else {
        await createProject(token, currentOrg.id, {
          name,
          slug,
          description,
          color,
          visibility,
          status: statusVal,
          workspace_id: wsId,
          start_date: startDate ? new Date(startDate).toISOString() : null,
          end_date: endDate ? new Date(endDate).toISOString() : null,
        });
      }
      setName('');
      setSlug('');
      setDescription('');
      setShowCreateModal(false);
    } catch (err: any) {
      setFormError(err.message || 'Failed to save project');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openDashboardModal = async (project: Project) => {
    setViewingDashboard(project);
    setDashboardTab('overview');
    if (!token || !currentOrg) return;
    setDashLoading(true);
    try {
      const [dash, mems, sets] = await Promise.all([
        projectApi.getProjectDashboard(token, currentOrg.id, project.id).catch(() => null),
        projectApi.getProjectMembers(token, currentOrg.id, project.id).catch(() => []),
        projectApi.getProjectSettings(token, currentOrg.id, project.id).catch(() => null),
      ]);
      setDashboardData(dash);
      setMembers(mems);
      setProjectSettings(sets);
    } catch (err) {
      console.error("Error loading dashboard details:", err);
    } finally {
      setDashLoading(false);
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!viewingDashboard || !inviteEmail || !token || !currentOrg) return;
    try {
      await projectApi.addProjectMember(token, currentOrg.id, viewingDashboard.id, inviteEmail, inviteRole);
      setInviteEmail('');
      const updated = await projectApi.getProjectMembers(token, currentOrg.id, viewingDashboard.id);
      setMembers(updated);
    } catch (err: any) {
      alert(err.message || 'Failed to add member to project');
    }
  };

  const handleRoleChange = async (userId: string, newRole: string) => {
    if (!viewingDashboard || !token || !currentOrg) return;
    try {
      await projectApi.updateProjectMember(token, currentOrg.id, viewingDashboard.id, userId, newRole);
      const updated = await projectApi.getProjectMembers(token, currentOrg.id, viewingDashboard.id);
      setMembers(updated);
    } catch (err: any) {
      alert(err.message || 'Failed to update member role');
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!viewingDashboard || !token || !currentOrg || !confirm("Remove member from project?")) return;
    try {
      await projectApi.removeProjectMember(token, currentOrg.id, viewingDashboard.id, userId);
      const updated = await projectApi.getProjectMembers(token, currentOrg.id, viewingDashboard.id);
      setMembers(updated);
    } catch (err: any) {
      alert(err.message || 'Failed to remove member');
    }
  };

  const handleUpdateSettings = async (settingsData: any) => {
    if (!viewingDashboard || !token || !currentOrg) return;
    try {
      const updated = await projectApi.updateProjectSettings(token, currentOrg.id, viewingDashboard.id, settingsData);
      setProjectSettings(updated);
    } catch (err: any) {
      alert(err.message || 'Failed to update project settings');
    }
  };

  return (
    <div className="space-y-3.5">
      {/* Header Banner */}
      <div className="flex flex-col gap-3 rounded-2xl border border-borderColor bg-bgCard p-3.5 sm:p-4 backdrop-blur-xl md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accentSubtle text-accentText shrink-0" aria-hidden="true">
            <Briefcase size={18} />
          </div>
          <div>
            <h1 className="text-base font-bold text-textPrimary">Project Management</h1>
            <p className="text-[11px] text-textMuted">
              Manage enterprise projects anchored to workspace: <span className="font-semibold text-textSecondary">{currentWorkspace?.name || 'All Workspaces'}</span>
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => {
            setName('');
            setSlug('');
            setDescription('');
            setEditingProject(null);
            setShowCreateModal(true);
          }}
          aria-label="Create new project"
          title="Create new project"
          className="flex items-center gap-1.5 rounded-xl bg-accent px-3 py-1.5 text-xs font-semibold text-white shadow-lg shadow-accent/20 hover:bg-accentHover transition-all shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          <Plus size={14} aria-hidden="true" />
          <span>New Project</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col gap-2.5 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {/* Workspace selector */}
          <select
            value={selectedWorkspaceId}
            onChange={(e) => setSelectedWorkspaceId(e.target.value)}
            aria-label="Filter by workspace"
            title="Filter by workspace"
            className="rounded-xl border border-borderColor bg-bgInput px-2.5 py-1.5 text-xs text-textPrimary outline-none focus:border-accent focus-visible:ring-2 focus-visible:ring-accent"
          >
            <option value="">All Workspaces</option>
            {workspaces.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>

          {/* Status filter pills */}
          <div role="tablist" aria-label="Filter projects by status" className="flex items-center gap-1 overflow-x-auto p-1 bg-bgTertiary rounded-xl border border-borderMuted">
            {['all', 'planning', 'active', 'on_hold', 'completed', 'archived'].map((st) => (
              <button
                key={st}
                type="button"
                role="tab"
                aria-selected={statusFilter === st}
                onClick={() => setStatusFilter(st)}
                className={`rounded-lg px-2 py-0.5 text-[10px] font-medium capitalize transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                  statusFilter === st
                    ? 'bg-accent text-white shadow-sm'
                    : 'text-textMuted hover:text-textPrimary hover:bg-bgHover'
                }`}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-2 h-3.5 w-3.5 text-textMuted" aria-hidden="true" />
          <label htmlFor="projects-search-input" className="sr-only">Search projects</label>
          <input
            id="projects-search-input"
            type="text"
            placeholder="Search projects..."
            aria-label="Search projects"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full md:w-60 rounded-xl border border-borderColor bg-bgInput py-1 pl-8 pr-3 text-xs text-textPrimary placeholder-textMuted outline-none focus:border-accent focus-visible:ring-2 focus-visible:ring-accent"
          />
        </div>
      </div>

      {/* Projects Grid Roster */}
      {loading && !projects.length ? (
        <div className="py-8 text-center text-textMuted text-xs">
          <Loader2 className="mx-auto mb-1.5 h-5 w-5 animate-spin text-accentText" />
          Loading project portfolio...
        </div>
      ) : projects.length === 0 ? (
        <EmptyState
          title="No projects yet"
          description="Projects organize conversations, documents, and knowledge into one collaborative space."
          icon={Briefcase}
          variant="card"
          primaryAction={{
            label: "Create Project",
            onClick: () => setShowCreateModal(true),
            icon: Plus
          }}
          secondaryAction={{
            label: "Browse Templates",
            onClick: () => setShowCreateModal(true),
            icon: Sparkles
          }}
        />
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(min(100%,270px),1fr))] gap-3 sm:gap-3.5">
          {projects.map((project) => {
            const stStyle = STATUS_COLORS[project.status] || STATUS_COLORS.active;
            return (
              <div
                key={project.id}
                className="group relative flex flex-col justify-between rounded-2xl border border-borderColor bg-bgCard p-3.5 backdrop-blur-md transition-all hover:border-accent/40 hover:bg-bgCardHover hover:shadow-xl hover:shadow-accent/5"
              >
                {/* Header Row */}
                <div>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2.5">
                      <div
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold text-white shadow-md shrink-0"
                        style={{ backgroundColor: project.color || '#3B82F6' }}
                      >
                        {project.icon ? project.icon : project.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <h3 className="text-xs font-semibold text-textPrimary group-hover:text-accentText transition-colors truncate">
                          {project.name}
                        </h3>
                        <span className="text-[9px] text-textMuted block truncate">slug: {project.slug}</span>
                      </div>
                    </div>

                    <span className={`rounded-full px-1.5 py-0.2 text-[9px] font-semibold border capitalize shrink-0 ${stStyle.bg} ${stStyle.text} ${stStyle.border}`}>
                      {project.status.replace('_', ' ')}
                    </span>
                  </div>

                  <p className="text-[11px] text-textMuted line-clamp-2 mb-2.5 min-h-[32px]">
                    {project.description || 'No description provided.'}
                  </p>
                </div>

                {/* Footer Metrics & Actions */}
                <div className="border-t border-borderMuted pt-2 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-[10px] text-textMuted">
                    <div className="flex items-center gap-1">
                      <Shield size={11} className="text-textMuted" />
                      <span className="capitalize">{project.visibility}</span>
                    </div>

                    {project.start_date && (
                      <div className="flex items-center gap-1">
                        <Calendar size={11} className="text-textMuted" />
                        <span>{new Date(project.start_date).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => openDashboardModal(project)}
                      className="rounded-lg bg-accentSubtle px-2.5 py-1 text-xs font-semibold text-accentText hover:bg-accent/20 transition-all"
                    >
                      Dashboard
                    </button>

                    {project.is_archived ? (
                      <button
                        onClick={() => restoreProject(token!, currentOrg!.id, project.id)}
                        className="rounded-lg p-1.5 text-textMuted hover:text-emerald-400 transition-colors"
                        title="Restore Project"
                      >
                        <RotateCcw size={14} />
                      </button>
                    ) : (
                      <button
                        onClick={() => archiveProject(token!, currentOrg!.id, project.id)}
                        className="rounded-lg p-1.5 text-textMuted hover:text-amber-400 transition-colors"
                        title="Archive Project"
                      >
                        <Archive size={14} />
                      </button>
                    )}

                    <button
                      onClick={() => {
                        if (confirm(`Delete project "${project.name}"?`)) {
                          deleteProject(token!, currentOrg!.id, project.id);
                        }
                      }}
                      className="rounded-lg p-1.5 text-textMuted hover:text-red-400 transition-colors"
                      title="Delete Project"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create / Edit Project Modal */}
      {(showCreateModal || editingProject) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-bgOverlay backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-lg rounded-2xl border border-borderColor bg-bgDialog p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-borderMuted pb-3">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-accentSubtle text-accentText">
                  <Briefcase size={18} />
                </div>
                <h3 className="text-base font-semibold text-textPrimary">
                  {editingProject ? 'Edit Project' : 'Create New Project'}
                </h3>
              </div>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingProject(null);
                }}
                className="text-textMuted hover:text-textPrimary"
              >
                <X size={16} />
              </button>
            </div>

            {formError && (
              <div className="rounded-xl border border-dangerBorder bg-dangerBg p-3 text-xs text-dangerText">
                {formError}
              </div>
            )}

            <form onSubmit={handleSaveProject} className="space-y-4">
              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-textSecondary mb-1">Project Name</label>
                  <input
                    type="text"
                    required
                    placeholder="Knowledge Base Engine"
                    value={name}
                    onChange={(e) => handleNameChange(e.target.value)}
                    className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-textSecondary mb-1">Slug</label>
                  <input
                    type="text"
                    required
                    placeholder="kb-engine"
                    value={slug}
                    onChange={(e) => setSlug(e.target.value)}
                    className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-textSecondary mb-1">Description</label>
                <textarea
                  rows={2}
                  placeholder="Outline the core goals and architectural scope."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                />
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                <div>
                  <label className="block text-xs font-medium text-textSecondary mb-1">Status</label>
                  <select
                    value={statusVal}
                    onChange={(e) => setStatusVal(e.target.value)}
                    className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent capitalize"
                  >
                    <option value="planning">Planning</option>
                    <option value="active">Active</option>
                    <option value="on_hold">On Hold</option>
                    <option value="completed">Completed</option>
                    <option value="archived">Archived</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-textSecondary mb-1">Visibility</label>
                  <select
                    value={visibility}
                    onChange={(e) => setVisibility(e.target.value)}
                    className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent capitalize"
                  >
                    <option value="private">Private</option>
                    <option value="public">Public</option>
                    <option value="restricted">Restricted</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-textSecondary mb-1">Accent Color</label>
                  <div className="flex items-center gap-1.5 pt-1">
                    {PROJECT_COLORS.map((c) => (
                      <button
                        key={c}
                        type="button"
                        onClick={() => setColor(c)}
                        className={`h-5 w-5 rounded-full transition-transform ${color === c ? 'scale-125 ring-2 ring-accent' : ''}`}
                        style={{ backgroundColor: c }}
                      />
                    ))}
                  </div>
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-textSecondary mb-1">Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-textSecondary mb-1">End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingProject(null);
                  }}
                  className="rounded-xl border border-borderColor px-4 py-2 text-xs font-medium text-textMuted hover:bg-bgHover hover:text-textPrimary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex items-center gap-1.5 rounded-xl bg-accent px-5 py-2 text-xs font-semibold text-white hover:bg-accentHover disabled:opacity-50"
                >
                  {isSubmitting ? <Loader2 size={14} className="animate-spin" /> : 'Save Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Project Dashboard Drawer Modal */}
      {viewingDashboard && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-bgOverlay backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div className="h-full w-full max-w-2xl rounded-2xl border border-borderColor bg-bgDialog p-6 shadow-2xl flex flex-col justify-between overflow-y-auto">
            {/* Top Bar */}
            <div>
              <div className="flex items-center justify-between border-b border-borderMuted pb-4 mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-10 w-10 items-center justify-center rounded-xl text-lg font-bold text-white"
                    style={{ backgroundColor: viewingDashboard.color || '#3B82F6' }}
                  >
                    {viewingDashboard.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-textPrimary">{viewingDashboard.name}</h2>
                    <p className="text-xs text-textMuted">slug: {viewingDashboard.slug} • status: <span className="capitalize text-accentText">{viewingDashboard.status}</span></p>
                  </div>
                </div>

                <button
                  onClick={() => setViewingDashboard(null)}
                  className="rounded-lg p-1.5 text-textMuted hover:text-textPrimary"
                >
                  <X size={18} />
                </button>
              </div>

              {/* Dashboard Sub Tabs */}
              <div className="flex border-b border-borderMuted gap-2 mb-6">
                {[
                  { id: 'overview', label: 'Overview Dashboard', icon: Briefcase },
                  { id: 'members', label: `Project Roster (${members.length})`, icon: Users },
                  { id: 'settings', label: 'Project Settings', icon: Settings },
                ].map((t) => {
                  const Icon = t.icon;
                  const isActive = dashboardTab === t.id;
                  return (
                    <button
                      key={t.id}
                      onClick={() => setDashboardTab(t.id as any)}
                      className={`flex items-center gap-2 px-3 py-2 text-xs font-semibold border-b-2 transition-all ${
                        isActive
                          ? 'border-accent text-accentText bg-accentSubtle'
                          : 'border-transparent text-textMuted hover:text-textPrimary'
                      }`}
                    >
                      <Icon size={14} />
                      <span>{t.label}</span>
                    </button>
                  );
                })}
              </div>

              {dashLoading ? (
                <div className="py-12 text-center text-textMuted">
                  <Loader2 className="mx-auto mb-2 h-6 w-6 animate-spin text-accentText" />
                  Loading dashboard statistics...
                </div>
              ) : (
                <>
                  {/* Tab 1: Overview */}
                  {dashboardTab === 'overview' && (
                    <div className="space-y-6">
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div className="rounded-xl border border-borderMuted bg-bgTertiary p-3.5">
                          <div className="text-[11px] font-medium text-textMuted mb-1">Members</div>
                          <div className="text-xl font-bold text-textPrimary">{dashboardData?.member_count || members.length}</div>
                        </div>

                        <div className="rounded-xl border border-borderMuted bg-bgTertiary p-3.5">
                          <div className="text-[11px] font-medium text-textMuted mb-1">Documents</div>
                          <div className="text-xl font-bold text-accentText">{dashboardData?.document_count || 0}</div>
                        </div>

                        <div className="rounded-xl border border-borderMuted bg-bgTertiary p-3.5">
                          <div className="text-[11px] font-medium text-textMuted mb-1">Chats</div>
                          <div className="text-xl font-bold text-accentText">{dashboardData?.chat_count || 0}</div>
                        </div>

                        <div className="rounded-xl border border-borderMuted bg-bgTertiary p-3.5">
                          <div className="text-[11px] font-medium text-textMuted mb-1">Tasks</div>
                          <div className="text-xl font-bold text-successText">{dashboardData?.task_count || 0}</div>
                        </div>
                      </div>

                      <div className="rounded-xl border border-borderMuted bg-bgTertiary p-4 space-y-3">
                        <h4 className="text-xs font-semibold text-textPrimary uppercase tracking-wider">Project Timeline & Metadata</h4>
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div>
                            <span className="text-textMuted block">Created On</span>
                            <span className="text-textPrimary font-medium">{new Date(viewingDashboard.created_at).toLocaleDateString()}</span>
                          </div>
                          <div>
                            <span className="text-textMuted block">Visibility</span>
                            <span className="text-textPrimary font-medium capitalize">{viewingDashboard.visibility}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tab 2: Members & Roster */}
                  {dashboardTab === 'members' && (
                    <div className="space-y-5">
                      <form onSubmit={handleAddMember} className="flex gap-2">
                        <input
                          type="email"
                          required
                          placeholder="teammate@company.com"
                          value={inviteEmail}
                          onChange={(e) => setInviteEmail(e.target.value)}
                          className="flex-1 rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent"
                        />
                        <select
                          value={inviteRole}
                          onChange={(e) => setInviteRole(e.target.value)}
                          className="rounded-xl border border-borderColor bg-bgInput px-3 py-2 text-xs text-textPrimary outline-none capitalize"
                        >
                          <option value="owner">Owner</option>
                          <option value="admin">Admin</option>
                          <option value="manager">Manager</option>
                          <option value="contributor">Contributor</option>
                          <option value="viewer">Viewer</option>
                        </select>
                        <button
                          type="submit"
                          className="rounded-xl bg-accent px-4 py-2 text-xs font-semibold text-white hover:bg-accentHover transition-all"
                        >
                          Add Member
                        </button>
                      </form>

                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs text-textSecondary">
                          <thead className="border-b border-borderMuted text-[11px] uppercase tracking-wider text-textMuted">
                            <tr>
                              <th className="pb-2 font-semibold">User</th>
                              <th className="pb-2 font-semibold">Role</th>
                              <th className="pb-2 font-semibold text-right">Actions</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-borderMuted">
                            {members.map((m) => (
                              <tr key={m.user_id}>
                                <td className="py-2.5">
                                  <div className="font-semibold text-textPrimary">{m.username || 'User'}</div>
                                  <div className="text-[11px] text-textMuted">{m.email}</div>
                                </td>
                                <td className="py-2.5">
                                  <select
                                    value={m.role}
                                    onChange={(e) => handleRoleChange(m.user_id, e.target.value)}
                                    className="rounded-lg border border-borderColor bg-bgInput px-2 py-1 text-xs text-textPrimary capitalize"
                                  >
                                    <option value="owner">Owner</option>
                                    <option value="admin">Admin</option>
                                    <option value="manager">Manager</option>
                                    <option value="contributor">Contributor</option>
                                    <option value="viewer">Viewer</option>
                                  </select>
                                </td>
                                <td className="py-2.5 text-right">
                                  <button
                                    onClick={() => handleRemoveMember(m.user_id)}
                                    className="text-dangerText hover:underline"
                                  >
                                    <Trash2 size={14} />
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Tab 3: Settings */}
                  {dashboardTab === 'settings' && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between rounded-xl border border-borderMuted bg-bgTertiary p-3.5">
                        <div>
                          <div className="text-xs font-semibold text-textPrimary">Enable AI Features</div>
                          <div className="text-[11px] text-textMuted">Allow AI indexing and contextual retrieval</div>
                        </div>
                        <input
                          type="checkbox"
                          checked={projectSettings?.enable_ai ?? true}
                          onChange={(e) => handleUpdateSettings({ enable_ai: e.target.checked })}
                          className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent"
                        />
                      </div>

                      <div className="flex items-center justify-between rounded-xl border border-borderMuted bg-bgTertiary p-3.5">
                        <div>
                          <div className="text-xs font-semibold text-textPrimary">Allow External Sharing</div>
                          <div className="text-[11px] text-textMuted">Permit external guest users to access project resources</div>
                        </div>
                        <input
                          type="checkbox"
                          checked={projectSettings?.allow_external_sharing ?? false}
                          onChange={(e) => handleUpdateSettings({ allow_external_sharing: e.target.checked })}
                          className="h-4 w-4 rounded border-borderMuted bg-bgInput text-accent"
                        />
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="border-t border-borderMuted pt-3 flex justify-end">
              <button
                onClick={() => setViewingDashboard(null)}
                className="rounded-xl border border-borderColor px-4 py-2 text-xs font-medium text-textMuted hover:bg-bgHover hover:text-textPrimary"
              >
                Close Dashboard
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectsPage;
