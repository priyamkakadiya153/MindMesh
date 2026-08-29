import React, { useState, useMemo } from 'react';
import { Users, Hash, Lock, Globe, X, Loader2, Search, Check, UserCheck } from 'lucide-react';

export interface OrgMemberItem {
  id?: string;
  user_id: string;
  username?: string;
  email: string;
  avatar_url?: string | null;
  status?: string;
  org_role?: string;
  workspace_role?: string;
  user?: {
    id: string;
    email: string;
    first_name?: string;
    last_name?: string;
    avatar_url?: string;
  };
}

interface GroupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: {
    name: string;
    description: string;
    type: 'group' | 'project_channel';
    visibility: 'public' | 'private' | 'read_only' | 'announcement';
    memberUserIds: string[];
  }) => Promise<void>;
  orgMembers?: OrgMemberItem[];
}

export const GroupModal: React.FC<GroupModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  orgMembers = []
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<'group' | 'project_channel'>('group');
  const [visibility, setVisibility] = useState<'public' | 'private' | 'read_only' | 'announcement'>('private');
  const [selectedMemberIds, setSelectedMemberIds] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filteredMembers = useMemo(() => {
    return (orgMembers || []).filter(m => {
      const uEmail = m.email || m.user?.email || '';
      const uName = m.username || (m.user?.first_name ? `${m.user.first_name} ${m.user.last_name || ''}` : uEmail);
      const query = searchQuery.toLowerCase().trim();
      if (!query) return true;
      return uName.toLowerCase().includes(query) || uEmail.toLowerCase().includes(query);
    });
  }, [orgMembers, searchQuery]);

  if (!isOpen) return null;

  const toggleMember = (userId: string) => {
    setSelectedMemberIds(prev =>
      prev.includes(userId) ? prev.filter(id => id !== userId) : [...prev, userId]
    );
  };

  const selectAllFiltered = () => {
    const filteredIds = filteredMembers.map(m => m.user_id || m.user?.id || m.id).filter(Boolean) as string[];
    const allSelected = filteredIds.every(id => selectedMemberIds.includes(id));
    if (allSelected) {
      setSelectedMemberIds(prev => prev.filter(id => !filteredIds.includes(id)));
    } else {
      setSelectedMemberIds(prev => Array.from(new Set([...prev, ...filteredIds])));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || isSubmitting) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await onSubmit({
        name: name.trim(),
        description: description.trim(),
        type,
        visibility,
        memberUserIds: selectedMemberIds
      });
      setName('');
      setDescription('');
      setSelectedMemberIds([]);
      setSearchQuery('');
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create group or channel');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-bgOverlay backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-bgDialog border border-borderColor rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-borderMuted pb-3">
          <div className="flex items-center space-x-2">
            {type === 'group' ? <Users className="w-5 h-5 text-accentText" /> : <Hash className="w-5 h-5 text-purple-500" />}
            <h3 className="text-base font-semibold text-textPrimary">
              Create New {type === 'group' ? 'Group Chat' : 'Project Channel'}
            </h3>
          </div>
          <button onClick={onClose} className="text-textMuted hover:text-textPrimary p-1 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="bg-dangerBg border border-dangerBorder text-dangerText text-xs p-3 rounded-xl">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Type Selector */}
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setType('group')}
              className={`flex items-center justify-center space-x-2 p-3 rounded-xl border text-xs font-medium transition-all ${
                type === 'group'
                  ? 'bg-accentSubtle border-accent text-accentText shadow-sm shadow-accent/20'
                  : 'bg-bgTertiary border-borderMuted text-textMuted hover:bg-bgHover'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Group Chat</span>
            </button>
            <button
              type="button"
              onClick={() => setType('project_channel')}
              className={`flex items-center justify-center space-x-2 p-3 rounded-xl border text-xs font-medium transition-all ${
                type === 'project_channel'
                  ? 'bg-purple-500/10 border-purple-500 text-purple-500 shadow-sm'
                  : 'bg-bgTertiary border-borderMuted text-textMuted hover:bg-bgHover'
              }`}
            >
              <Hash className="w-4 h-4" />
              <span>Project Channel</span>
            </button>
          </div>

          {/* Name */}
          <div>
            <label className="block text-xs font-medium text-textSecondary mb-1">
              {type === 'group' ? 'Group Name' : 'Channel Name'} *
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder={type === 'group' ? 'e.g. Executive Board' : 'e.g. #engineering-architecture'}
              className="w-full bg-bgInput text-textPrimary placeholder-textMuted text-xs rounded-xl px-3 py-2.5 border border-borderColor focus:outline-none focus:border-accent"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium text-textSecondary mb-1">Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={2}
              placeholder="What is the purpose of this group or channel?"
              className="w-full bg-bgInput text-textPrimary placeholder-textMuted text-xs rounded-xl px-3 py-2.5 border border-borderColor focus:outline-none focus:border-accent resize-none"
            />
          </div>

          {/* Visibility */}
          <div>
            <label className="block text-xs font-medium text-textSecondary mb-1">Privacy & Access</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setVisibility('private')}
                className={`flex items-center space-x-2 p-2.5 rounded-xl border text-xs text-left ${
                  visibility === 'private'
                    ? 'bg-accentSubtle border-accent text-accentText'
                    : 'bg-bgTertiary border-borderMuted text-textMuted'
                }`}
              >
                <Lock className="w-4 h-4 shrink-0" />
                <div>
                  <p className="font-semibold text-[11px]">Private</p>
                  <p className="text-[9px] text-textMuted">By invite only</p>
                </div>
              </button>
              <button
                type="button"
                onClick={() => setVisibility('public')}
                className={`flex items-center space-x-2 p-2.5 rounded-xl border text-xs text-left ${
                  visibility === 'public'
                    ? 'bg-successBg border-successBorder text-successText'
                    : 'bg-bgTertiary border-borderMuted text-textMuted'
                }`}
              >
                <Globe className="w-4 h-4 shrink-0" />
                <div>
                  <p className="font-semibold text-[11px]">Public</p>
                  <p className="text-[9px] text-textMuted">Open to org members</p>
                </div>
              </button>
            </div>
          </div>

          {/* Add Initial Members (for Group Chat) */}
          {type === 'group' && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-textSecondary">
                  Add Members ({selectedMemberIds.length} selected)
                </label>
                {filteredMembers.length > 0 && (
                  <button
                    type="button"
                    onClick={selectAllFiltered}
                    className="text-[11px] text-accentText hover:underline font-medium"
                  >
                    {filteredMembers.every(m => selectedMemberIds.includes(m.user_id || m.user?.id || '')) ? 'Deselect All' : 'Select All'}
                  </button>
                )}
              </div>

              {/* Search Filter Box */}
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-textMuted absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search team members by name or email..."
                  className="w-full bg-bgInput text-textPrimary placeholder-textMuted text-xs rounded-xl pl-9 pr-3 py-2 border border-borderColor focus:outline-none focus:border-accent"
                />
              </div>

              {/* Members List Container */}
              <div className="max-h-44 overflow-y-auto space-y-1.5 p-2 bg-bgTertiary border border-borderMuted rounded-xl">
                {orgMembers.length === 0 ? (
                  <div className="p-4 text-center text-textMuted text-xs space-y-1">
                    <Users className="w-5 h-5 mx-auto text-textMuted" />
                    <p>No other active members found in organization.</p>
                  </div>
                ) : filteredMembers.length === 0 ? (
                  <div className="p-4 text-center text-textMuted text-xs">
                    No members matching "{searchQuery}".
                  </div>
                ) : (
                  filteredMembers.map(m => {
                    const uId = m.user_id || m.user?.id || m.id || '';
                    const uEmail = m.email || m.user?.email || '';
                    const uName = m.username || (m.user?.first_name ? `${m.user.first_name} ${m.user.last_name || ''}` : uEmail);
                    const role = m.org_role || m.workspace_role || 'member';
                    const isSelected = selectedMemberIds.includes(uId);

                    return (
                      <div
                        key={uId}
                        onClick={() => toggleMember(uId)}
                        className={`w-full flex items-center justify-between p-2 rounded-xl text-xs cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-accentSubtle text-accentText border border-accent/40 shadow-sm'
                            : 'hover:bg-bgHover text-textSecondary border border-transparent'
                        }`}
                      >
                        <div className="flex items-center space-x-2.5 min-w-0 pr-2">
                          <div className="w-7 h-7 rounded-full bg-bgCard border border-borderMuted text-textPrimary font-semibold text-xs flex items-center justify-center shrink-0">
                            {uName.charAt(0).toUpperCase()}
                          </div>
                          <div className="min-w-0 text-left">
                            <p className="font-semibold text-textPrimary truncate text-xs">{uName}</p>
                            <p className="text-[10px] text-textMuted truncate">{uEmail}</p>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 shrink-0">
                          <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-bgCard text-textMuted border border-borderMuted">
                            {role}
                          </span>
                          <div className={`w-4 h-4 rounded flex items-center justify-center border ${
                            isSelected ? 'bg-accent border-accent text-white' : 'border-borderColor bg-bgInput'
                          }`}>
                            {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}

          {/* Footer Actions */}
          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-borderMuted">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-bgTertiary hover:bg-bgHover text-textMuted hover:text-textPrimary rounded-xl text-xs font-medium transition-colors border border-borderMuted"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name.trim() || isSubmitting}
              className="px-5 py-2 bg-accent hover:bg-accentHover text-white rounded-xl text-xs font-semibold shadow-lg shadow-accent/20 transition-all flex items-center space-x-1.5"
            >
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              <span>Create {type === 'group' ? 'Group' : 'Channel'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
