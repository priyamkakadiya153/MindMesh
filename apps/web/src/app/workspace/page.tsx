import React, { useState, useEffect } from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { useWorkspaceStore } from '../../features/workspace/store';
import { WorkspaceCard } from '../../features/dashboard/components/WorkspaceCard';
import { EmptyState } from '../../shared/components/EmptyState';
import { Plus, Grid, RefreshCw, AlertCircle } from 'lucide-react';

export function WorkspacePage() {
  const { token, currentOrg } = useAuth();
  const {
    workspaces,
    currentWorkspace,
    selectWorkspace,
    createWorkspace,
    fetchWorkspaces,
    loading,
    error
  } = useWorkspaceStore();

  const [newWsName, setNewWsName] = useState('');
  const [newWsSlug, setNewWsSlug] = useState('');
  const [wsMessage, setWsMessage] = useState('');
  const [wsLoading, setWsLoading] = useState(false);

  useEffect(() => {
    if (token && currentOrg) {
      fetchWorkspaces(token, currentOrg.id);
    }
  }, [token, currentOrg, fetchWorkspaces]);

  // Live auto-synchronization when workspace, project, or document changes
  useEffect(() => {
    const handleDataChange = () => {
      if (token && currentOrg) {
        fetchWorkspaces(token, currentOrg.id);
      }
    };

    window.addEventListener('mindmesh:workspace-changed', handleDataChange);
    window.addEventListener('mindmesh:project-changed', handleDataChange);
    window.addEventListener('mindmesh:document-changed', handleDataChange);
    return () => {
      window.removeEventListener('mindmesh:workspace-changed', handleDataChange);
      window.removeEventListener('mindmesh:project-changed', handleDataChange);
      window.removeEventListener('mindmesh:document-changed', handleDataChange);
    };
  }, [token, currentOrg, fetchWorkspaces]);

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWsName || !newWsSlug || !token || !currentOrg) return;
    setWsLoading(true);
    setWsMessage('');

    try {
      await createWorkspace(token, currentOrg.id, newWsName, newWsSlug);
      setWsMessage(`Successfully created ${newWsName}!`);
      setNewWsName('');
      setNewWsSlug('');
      fetchWorkspaces(token, currentOrg.id);
    } catch (err: any) {
      setWsMessage(`Error: ${err.message || 'Failed to create workspace'}`);
    } finally {
      setWsLoading(false);
    }
  };

  const triggerRefresh = () => {
    if (token && currentOrg) {
      fetchWorkspaces(token, currentOrg.id);
    }
  };

  return (
    <div className="space-y-4">
      <h1 className="sr-only">Workspace Management</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass-panel p-4 bg-bgCard border border-borderColor lg:col-span-1 h-fit rounded-2xl">
          <h2 className="text-xs font-bold text-textPrimary mb-2.5 flex items-center gap-2">
            <Plus size={15} className="text-accentText" aria-hidden="true" />
            <span>Add New Workspace</span>
          </h2>
          
          <form onSubmit={handleCreateWorkspace} className="space-y-2.5">
            <div>
              <label htmlFor="ws-page-name" className="block text-xs text-textMuted mb-1">Workspace Name</label>
              <input
                id="ws-page-name"
                type="text"
                required
                value={newWsName}
                onChange={(e) => {
                  setNewWsName(e.target.value);
                  setNewWsSlug(e.target.value.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''));
                }}
                placeholder="Workspace name..."
                className="w-full px-3 py-1.5 bg-bgInput border border-borderColor rounded-xl text-xs text-textPrimary placeholder-textMuted focus:outline-none focus:border-accent/40 focus-visible:ring-2 focus-visible:ring-accent"
              />
            </div>
            <div>
              <label htmlFor="ws-page-slug" className="block text-xs text-textMuted mb-1">Workspace Slug</label>
              <input
                id="ws-page-slug"
                type="text"
                required
                value={newWsSlug}
                onChange={(e) => setNewWsSlug(e.target.value)}
                placeholder="workspace-slug"
                className="w-full px-3 py-1.5 bg-bgInput border border-borderColor rounded-xl text-xs text-textPrimary placeholder-textMuted focus:outline-none focus:border-accent/40 focus-visible:ring-2 focus-visible:ring-accent"
              />
            </div>

            {wsMessage && (
              <div 
                role="status"
                aria-live="polite"
                className={`p-2 rounded-lg text-[10px] font-medium flex items-center gap-2 ${
                  wsMessage.startsWith('Error') 
                    ? 'bg-dangerBg text-dangerText border border-dangerBorder' 
                    : 'bg-successBg text-successText border border-successBorder'
                }`}
              >
                <AlertCircle size={12} aria-hidden="true" />
                <span>{wsMessage}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={wsLoading}
              className="w-full py-2 bg-accent hover:bg-accentHover disabled:bg-accent/40 text-white text-xs font-bold rounded-xl border border-accent/20 shadow-lg shadow-accent/10 transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              {wsLoading ? 'Creating Workspace...' : 'Create Workspace'}
            </button>
          </form>
        </div>

        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-semibold text-textPrimary flex items-center gap-2">
              <Grid size={15} className="text-accentText" aria-hidden="true" />
              <span>Active Workspaces</span>
            </h2>
            <button 
              type="button"
              onClick={triggerRefresh}
              aria-label="Refresh workspaces list"
              title="Refresh workspaces list"
              className="p-1.5 rounded-lg bg-bgTertiary text-textMuted hover:text-accentText border border-borderMuted transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <RefreshCw size={12} className={loading ? 'animate-spin' : ''} aria-hidden="true" />
            </button>
          </div>

        {error && (
          <div className="p-3 mb-4 bg-rose-500/10 text-rose-400 rounded-xl text-xs flex items-center gap-2">
            <AlertCircle size={14} />
            <span>Failed to sync workspaces: {error}</span>
          </div>
        )}

        {workspaces.length === 0 ? (
          <EmptyState
            title="No workspaces"
            description="Workspaces help separate teams, departments, or projects."
            icon={Grid}
            variant="card"
            primaryAction={{
              label: "Create Workspace",
              onClick: () => {
                const el = document.querySelector('input[placeholder*="Workspace name"]') as HTMLInputElement;
                if (el) el.focus();
              },
              icon: Plus
            }}
          />
        ) : (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(min(100%,240px),1fr))] gap-4">
            {workspaces.map((ws) => (
              <WorkspaceCard
                key={ws.id}
                workspace={ws}
                isActive={currentWorkspace?.id === ws.id}
                projectsCount={ws.projects_count ?? 0}
                documentsCount={ws.documents_count ?? 0}
                membersCount={ws.members_count ?? 1}
                onSelect={() => selectWorkspace(ws)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  </div>
);
}
export default WorkspacePage;
