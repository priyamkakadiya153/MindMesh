import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../auth/auth-provider';
import { useWorkspaceStore, Workspace } from '../../workspace/store';
import { Layers, Loader2, Plus, AlertCircle, Check, ChevronDown, Settings, Hash, Compass, Code, Shield } from 'lucide-react';
import { useNavigationStore } from '../store';

const WORKSPACE_COLORS = ['#3B82F6', '#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#EF4444', '#06B6D4'];

export function WorkspaceSwitcher() {
  const { token, currentOrg } = useAuth();
  const { workspaces, currentWorkspace, selectWorkspace, fetchWorkspaces, createWorkspace, loading, error } = useWorkspaceStore();
  const { setActiveTab } = useNavigationStore();

  const [isOpen, setIsOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Form state
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [selectedColor, setSelectedColor] = useState('#3B82F6');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (token && currentOrg) {
      fetchWorkspaces(token, currentOrg.id);
    }
  }, [token, currentOrg, fetchWorkspaces]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleNameChange = (val: string) => {
    setName(val);
    setSlug(val.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, ''));
  };

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !token || !currentOrg) return;
    setIsSubmitting(true);
    setFormError(null);
    try {
      const created = await createWorkspace(token, currentOrg.id, name, slug || name.toLowerCase());
      selectWorkspace(created);
      setName('');
      setSlug('');
      setDescription('');
      setShowCreateModal(false);
      setIsOpen(false);
    } catch (err: any) {
      setFormError(err.message || 'Failed to create workspace');
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (showCreateModal) setShowCreateModal(false);
        else if (isOpen) setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, showCreateModal]);

  if (loading && !workspaces.length) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-borderColor bg-bgCard px-2.5 sm:px-3 min-h-[44px] sm:min-h-[38px] text-xs text-textMuted shrink-0">
        <Loader2 className="h-3.5 w-3.5 animate-spin text-accent" aria-hidden="true" />
        <span className="hidden sm:inline">Loading Workspaces...</span>
      </div>
    );
  }

  return (
    <div className="relative shrink-0" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Select workspace"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        title="Select workspace"
        className="flex items-center gap-1.5 sm:gap-2 rounded-xl border border-borderColor bg-bgCard px-2.5 sm:px-3 min-h-[44px] sm:min-h-[38px] backdrop-blur-md transition-all duration-150 hover:bg-bgHover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent active:scale-95 group max-w-[130px] sm:max-w-[190px] md:max-w-[220px]"
      >
        <div className="flex items-center justify-center shrink-0">
          {currentWorkspace?.color ? (
            <span
              className="h-2.5 w-2.5 rounded-full shadow-sm"
              style={{ backgroundColor: currentWorkspace.color }}
              aria-hidden="true"
            />
          ) : (
            <Layers size={13} className="text-accent" aria-hidden="true" />
          )}
        </div>

        <span className="text-xs font-semibold text-textPrimary max-w-[70px] sm:max-w-[120px] md:max-w-[150px] truncate">
          {currentWorkspace?.name || 'Select Workspace'}
        </span>

        {currentWorkspace?.is_default && (
          <span className="hidden sm:inline-block rounded bg-bgTertiary px-1 py-0.2 text-[9px] font-medium text-textMuted shrink-0">
            Default
          </span>
        )}

        <ChevronDown className={`h-3.5 w-3.5 text-textMuted transition-transform duration-200 shrink-0 ${isOpen ? 'rotate-180 text-accent' : ''}`} aria-hidden="true" />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div 
          role="listbox"
          aria-label="Workspaces list"
          className="absolute left-0 mt-2 w-64 rounded-2xl border border-borderColor bg-bgDialog p-2 shadow-2xl backdrop-blur-xl z-50 animate-in fade-in duration-150 text-textPrimary"
        >
          <div className="px-2 py-1 mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-textMuted">
              Workspaces in {currentOrg?.name}
            </span>
          </div>

          <div className="max-h-48 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
            {workspaces.map((ws) => {
              const isActive = currentWorkspace?.id === ws.id;
              return (
                <button
                  key={ws.id}
                  type="button"
                  role="option"
                  aria-selected={isActive}
                  onClick={() => {
                    selectWorkspace(ws);
                    setIsOpen(false);
                  }}
                  className={`flex w-full items-center justify-between rounded-xl px-2.5 py-1.5 text-left transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                    isActive
                      ? 'bg-accentSubtle border border-accent/30 text-accentText font-semibold'
                      : 'hover:bg-bgHover text-textSecondary hover:text-textPrimary font-medium'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: ws.color || '#3B82F6' }}
                      aria-hidden="true"
                    />
                    <span className="text-xs truncate">{ws.name}</span>
                    {ws.is_default && (
                      <span className="text-[9px] text-textMuted font-normal">default</span>
                    )}
                  </div>
                  {isActive && <Check className="h-3.5 w-3.5 text-accent" aria-hidden="true" />}
                </button>
              );
            })}
          </div>

          <div className="my-1.5 border-t border-borderMuted" />

          <div className="space-y-1">
            <button
              type="button"
              onClick={() => {
                setActiveTab('workspaces' as any);
                setIsOpen(false);
              }}
              className="flex w-full items-center gap-2 rounded-xl px-2.5 py-1.5 text-xs font-medium text-textSecondary hover:bg-bgHover hover:text-textPrimary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent transition-all"
            >
              <Settings className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Workspace Management</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setShowCreateModal(true);
                setIsOpen(false);
              }}
              className="flex w-full items-center gap-2 rounded-xl bg-accentSubtle px-2.5 py-1.5 text-xs font-semibold text-accentText hover:bg-accent/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent transition-all"
            >
              <Plus className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Create New Workspace</span>
            </button>
          </div>
        </div>
      )}

      {/* Create Workspace Modal */}
      {showCreateModal && (
        <div 
          role="dialog"
          aria-modal="true"
          aria-labelledby="create-workspace-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-bgOverlay backdrop-blur-md p-4 animate-in fade-in duration-200"
        >
          <div className="w-full max-w-md rounded-2xl border border-borderColor bg-bgDialog p-6 shadow-2xl text-textPrimary">
            <div className="flex items-center justify-between border-b border-borderColor pb-4 mb-4">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-accentSubtle text-accentText">
                  <Layers size={18} aria-hidden="true" />
                </div>
                <div>
                  <h3 id="create-workspace-title" className="text-base font-semibold text-textPrimary">Create Workspace</h3>
                  <p className="text-xs text-textMuted">Add a workspace to {currentOrg?.name}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                aria-label="Close create workspace modal"
                title="Close dialog"
                className="text-textMuted hover:text-textPrimary text-sm p-1 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              >
                ✕
              </button>
            </div>

            {formError && (
              <div role="alert" className="mb-4 rounded-xl border border-dangerBorder bg-dangerBg p-3 text-xs text-dangerText">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateWorkspace} className="space-y-4">
              <div>
                <label htmlFor="ws-name-input" className="block text-xs font-medium text-textSecondary mb-1">Workspace Name</label>
                <input
                  id="ws-name-input"
                  type="text"
                  required
                  placeholder="Development, Marketing, Sales..."
                  value={name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  className="w-full rounded-xl border border-borderColor bg-bgInput px-3.5 py-2 text-xs text-textPrimary placeholder-textMuted focus:border-accent focus-visible:ring-2 focus-visible:ring-accent outline-none"
                />
              </div>

              <div>
                <label id="color-theme-label" className="block text-xs font-medium text-textSecondary mb-1">Color Theme</label>
                <div role="group" aria-labelledby="color-theme-label" className="flex items-center gap-2">
                  {WORKSPACE_COLORS.map((c) => (
                    <button
                      key={c}
                      type="button"
                      aria-label={`Select color ${c}`}
                      onClick={() => setSelectedColor(c)}
                      className={`h-6 w-6 rounded-full transition-transform focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${selectedColor === c ? 'scale-125 ring-2 ring-accent ring-offset-2 ring-offset-bgCard' : 'hover:scale-110'}`}
                      style={{ backgroundColor: c }}
                    />
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-xl border border-borderColor px-4 py-2 text-xs font-medium text-textSecondary hover:bg-bgHover hover:text-textPrimary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex items-center gap-1.5 rounded-xl bg-accent px-4 py-2 text-xs font-semibold text-white hover:bg-accentHover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent transition-all disabled:opacity-50"
                >
                  {isSubmitting ? 'Creating...' : 'Create Workspace'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default WorkspaceSwitcher;
