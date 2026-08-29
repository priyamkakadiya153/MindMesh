import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { Building, Check, ChevronDown, Plus, Settings, Search, Sparkles, ShieldCheck } from 'lucide-react';
import { useNavigationStore } from '../../features/navigation/store';

export const OrganizationSwitcher: React.FC = () => {
  const { currentOrg, organizations, switchOrganization, createOrg } = useAuth();
  const { setActiveTab } = useNavigationStore();

  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Create Org Modal Form State
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const dropdownRef = useRef<HTMLDivElement>(null);

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
    if (!slug || slug === val.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').slice(0, -1)) {
      setSlug(val.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, ''));
    }
  };

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !slug) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await createOrg(name, slug);
      setName('');
      setSlug('');
      setDescription('');
      setShowCreateModal(false);
      setIsOpen(false);
    } catch (err: any) {
      setError(err.message || 'Failed to create organization');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredOrgs = organizations.filter(o =>
    o.name.toLowerCase().includes(search.toLowerCase()) ||
    o.slug.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2.5 rounded-xl border border-white/[0.08] bg-slate-900/60 px-3 py-1.5 backdrop-blur-md transition-all hover:border-violet-500/40 hover:bg-slate-900/90 hover:shadow-lg hover:shadow-violet-500/5 group"
      >
        <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 text-xs font-bold text-white shadow-sm">
          {currentOrg?.logo_url ? (
            <img src={currentOrg.logo_url} alt={currentOrg.name} className="h-full w-full rounded-lg object-cover" />
          ) : (
            currentOrg?.name?.charAt(0).toUpperCase() || <Building className="h-3.5 w-3.5" />
          )}
        </div>

        <div className="flex flex-col text-left">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-slate-100 group-hover:text-white max-w-[120px] truncate">
              {currentOrg?.name || 'Select Org'}
            </span>
            {currentOrg?.is_personal && (
              <span className="rounded bg-violet-500/20 px-1 py-0.2 text-[9px] font-medium text-violet-300">
                Personal
              </span>
            )}
          </div>
        </div>

        <ChevronDown className={`h-3.5 w-3.5 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180 text-violet-400' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute left-0 mt-2 w-72 rounded-2xl border border-white/10 bg-slate-950/95 p-2 shadow-2xl backdrop-blur-xl z-50 animate-in fade-in slide-in-from-top-2 duration-150">
          {/* Header Search */}
          <div className="relative mb-2 px-1">
            <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              placeholder="Search organizations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-900/80 py-1.5 pl-8 pr-3 text-xs text-slate-200 placeholder-slate-500 outline-none focus:border-violet-500/50"
            />
          </div>

          {/* Org List */}
          <div className="max-h-52 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
            {filteredOrgs.length === 0 ? (
              <div className="py-3 text-center text-xs text-slate-500">No organizations found</div>
            ) : (
              filteredOrgs.map((org) => {
                const isActive = currentOrg?.id === org.id;
                return (
                  <button
                    key={org.id}
                    onClick={() => {
                      switchOrganization(org);
                      setIsOpen(false);
                    }}
                    className={`flex w-full items-center justify-between rounded-xl px-2.5 py-2 text-left transition-all ${
                      isActive
                        ? 'bg-violet-600/15 border border-violet-500/30 text-white'
                        : 'hover:bg-slate-900/80 text-slate-300 hover:text-slate-100'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <div className={`flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold ${
                        isActive ? 'bg-violet-600 text-white' : 'bg-slate-800 text-slate-400'
                      }`}>
                        {org.logo_url ? (
                          <img src={org.logo_url} alt={org.name} className="h-full w-full rounded-lg object-cover" />
                        ) : (
                          org.name.charAt(0).toUpperCase()
                        )}
                      </div>
                      <div className="flex flex-col truncate">
                        <span className="text-xs font-medium truncate">{org.name}</span>
                        <span className="text-[10px] text-slate-500 capitalize">{org.role || (org.is_personal ? 'Personal' : 'Member')}</span>
                      </div>
                    </div>

                    {isActive && <Check className="h-3.5 w-3.5 text-violet-400" />}
                  </button>
                );
              })
            )}
          </div>

          <div className="my-1.5 border-t border-slate-800/80" />

          {/* Action Buttons */}
          <div className="space-y-1">
            <button
              onClick={() => {
                setActiveTab('organization' as any);
                setIsOpen(false);
              }}
              className="flex w-full items-center gap-2 rounded-xl px-2.5 py-1.5 text-xs font-medium text-slate-400 hover:bg-slate-900 hover:text-slate-200 transition-all"
            >
              <Settings className="h-3.5 w-3.5 text-slate-400" />
              <span>Organization Settings</span>
            </button>

            <button
              onClick={() => {
                setShowCreateModal(true);
                setIsOpen(false);
              }}
              className="flex w-full items-center gap-2 rounded-xl bg-violet-600/10 px-2.5 py-1.5 text-xs font-semibold text-violet-400 hover:bg-violet-600/20 hover:text-violet-300 transition-all"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Create New Organization</span>
            </button>
          </div>
        </div>
      )}

      {/* Create Organization Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-950 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-violet-600/20 text-violet-400">
                  <Building size={18} />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Create Organization</h3>
                  <p className="text-xs text-slate-400">Set up a new multi-tenant organization</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            {error && (
              <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-xs text-red-400">
                {error}
              </div>
            )}

            <form onSubmit={handleCreateOrg} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Organization Name</label>
                <input
                  type="text"
                  required
                  placeholder="Acme Corporation"
                  value={name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:border-violet-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Organization Slug (URL identifier)</label>
                <input
                  type="text"
                  required
                  placeholder="acme-corp"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-slate-300 placeholder-slate-500 focus:border-violet-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description (Optional)</label>
                <textarea
                  placeholder="Enterprise workspace for Acme teams"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  className="w-full rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:border-violet-500 outline-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-xl border border-slate-800 px-4 py-2 text-xs font-medium text-slate-400 hover:bg-slate-900 hover:text-white transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex items-center gap-1.5 rounded-xl bg-violet-600 px-4 py-2 text-xs font-semibold text-white hover:bg-violet-500 transition-all disabled:opacity-50"
                >
                  {isSubmitting ? 'Creating...' : 'Create Organization'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
