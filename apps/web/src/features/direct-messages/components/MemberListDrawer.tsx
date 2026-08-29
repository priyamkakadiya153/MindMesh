import React, { useState } from 'react';
import { Conversation } from '../types';
import { OnlineBadge } from './OnlineBadge';
import { Users, Shield, UserPlus, UserMinus, X, Archive, Search, LogOut, Trash2, Edit3, Check, AlertTriangle } from 'lucide-react';

interface MemberListDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  conversation: Conversation;
  currentUserId: string;
  orgMembers?: any[];
  onAddMember?: (userId: string) => Promise<void>;
  onRemoveMember?: (userId: string) => Promise<void>;
  onUpdateRole?: (userId: string, role: string) => Promise<void>;
  onArchiveGroup?: () => Promise<void>;
  onDeleteGroup?: () => Promise<void>;
  onUpdateGroup?: (name: string, description?: string) => Promise<void>;
}

export const MemberListDrawer: React.FC<MemberListDrawerProps> = ({
  isOpen,
  onClose,
  conversation,
  currentUserId,
  orgMembers = [],
  onAddMember,
  onRemoveMember,
  onUpdateRole,
  onArchiveGroup,
  onDeleteGroup,
  onUpdateGroup
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedUserToAdd, setSelectedUserToAdd] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  // Edit / Rename state
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(conversation.name || '');
  const [editDescription, setEditDescription] = useState(conversation.description || '');
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  // Confirmation Modals
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmName, setDeleteConfirmName] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

  if (!isOpen) return null;

  const currentMember = conversation.members?.find(m => (m.user_id || m.id) === currentUserId);
  const isOwner = conversation.owner_id === currentUserId || currentMember?.role === 'owner';
  const isOwnerOrAdmin = isOwner || currentMember?.role === 'admin';

  const filteredMembers = (conversation.members || []).filter(m =>
    (m.full_name?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
    (m.email?.toLowerCase() || '').includes(searchQuery.toLowerCase())
  );

  const existingMemberUserIds = new Set((conversation.members || []).map(m => m.user_id));
  const availableToAdd = orgMembers.filter(m => !existingMemberUserIds.has(m.user?.id || m.user_id));

  const handleAdd = async () => {
    if (!selectedUserToAdd || !onAddMember) return;
    setIsAdding(true);
    try {
      await onAddMember(selectedUserToAdd);
      setSelectedUserToAdd('');
    } catch (err) {
      console.error(err);
    } finally {
      setIsAdding(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!editName.trim() || !onUpdateGroup) return;
    setIsSavingEdit(true);
    try {
      await onUpdateGroup(editName.trim(), editDescription.trim());
      setIsEditing(false);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSavingEdit(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (deleteConfirmName.trim() !== conversation.name || !onDeleteGroup) return;
    setIsDeleting(true);
    try {
      await onDeleteGroup();
      setShowDeleteModal(false);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleConfirmLeave = async () => {
    if (!onRemoveMember) return;
    setIsLeaving(true);
    try {
      await onRemoveMember(currentUserId);
      setShowLeaveModal(false);
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsLeaving(false);
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'owner':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      case 'admin':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'moderator':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="w-80 bg-bgSidebar border-l border-borderColor flex flex-col h-full z-40 select-none relative">
      {/* Header */}
      <div className="p-4 border-b border-borderMuted flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Users className="w-5 h-5 text-accentText" />
          <h3 className="font-semibold text-textPrimary text-sm">Group Details</h3>
        </div>
        <button onClick={onClose} className="p-1 text-textMuted hover:text-textPrimary rounded-lg">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* Info Card / Edit Card */}
        <div className="bg-bgCard border border-borderColor rounded-xl p-3.5 space-y-2">
          {isEditing ? (
            <div className="space-y-2">
              <label className="text-[11px] font-semibold text-textSecondary">Group Name</label>
              <input
                type="text"
                value={editName}
                onChange={e => setEditName(e.target.value)}
                className="w-full bg-bgInput text-textPrimary text-xs rounded-lg px-2.5 py-1.5 border border-borderColor focus:outline-none focus:border-accent"
              />
              <label className="text-[11px] font-semibold text-textSecondary">Description</label>
              <textarea
                value={editDescription}
                onChange={e => setEditDescription(e.target.value)}
                rows={2}
                className="w-full bg-bgInput text-textPrimary text-xs rounded-lg px-2.5 py-1.5 border border-borderColor focus:outline-none focus:border-accent resize-none"
              />
              <div className="flex justify-end space-x-2 pt-1">
                <button
                  onClick={() => setIsEditing(false)}
                  className="px-2.5 py-1 text-xs text-textMuted hover:text-textPrimary rounded-lg"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  disabled={!editName.trim() || isSavingEdit}
                  className="px-3 py-1 bg-accent hover:bg-accentHover text-white rounded-lg text-xs font-semibold flex items-center space-x-1 disabled:opacity-50"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Save</span>
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className="flex items-start justify-between">
                <h4 className="font-semibold text-xs text-textPrimary">{conversation.name}</h4>
                {isOwnerOrAdmin && onUpdateGroup && (
                  <button
                    onClick={() => {
                      setEditName(conversation.name || '');
                      setEditDescription(conversation.description || '');
                      setIsEditing(true);
                    }}
                    className="p-1 text-textMuted hover:text-accentText rounded-lg"
                    title="Edit Group Info"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
              {conversation.description && (
                <p className="text-[11px] text-textMuted leading-relaxed">{conversation.description}</p>
              )}
              <div className="flex items-center justify-between text-[10px] text-textMuted pt-1 border-t border-borderMuted">
                <span>Type: {conversation.type}</span>
                <span className="capitalize">Visibility: {conversation.visibility}</span>
              </div>
            </>
          )}
        </div>

        {/* Add Member Section */}
        {isOwnerOrAdmin && onAddMember && availableToAdd.length > 0 && (
          <div className="space-y-2">
            <h5 className="text-xs font-semibold text-textSecondary flex items-center space-x-1.5">
              <UserPlus className="w-3.5 h-3.5 text-accentText" />
              <span>Invite Member</span>
            </h5>
            <div className="flex space-x-2">
              <select
                value={selectedUserToAdd}
                onChange={e => setSelectedUserToAdd(e.target.value)}
                className="flex-1 bg-bgInput text-textPrimary text-xs rounded-xl px-2.5 py-2 border border-borderColor focus:outline-none focus:border-accent"
              >
                <option value="">Select member...</option>
                {availableToAdd.map(m => {
                  const uId = m.user_id || m.user?.id || m.id;
                  const uEmail = m.email || m.user?.email || '';
                  const uName = m.username || (m.user?.first_name ? `${m.user.first_name} ${m.user.last_name || ''}` : uEmail);
                  return (
                    <option key={uId} value={uId}>
                      {uName} ({uEmail})
                    </option>
                  );
                })}
              </select>
              <button
                onClick={handleAdd}
                disabled={!selectedUserToAdd || isAdding}
                className="px-3 py-2 bg-accent hover:bg-accentHover text-white rounded-xl text-xs font-semibold disabled:opacity-50 transition-all"
              >
                Add
              </button>
            </div>
          </div>
        )}

        {/* Member Search */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h5 className="text-xs font-semibold text-textSecondary">
              Members ({conversation.members?.length || 0})
            </h5>
          </div>
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-textMuted absolute left-2.5 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search members..."
              className="w-full bg-bgInput text-textPrimary placeholder-textMuted text-[11px] rounded-lg pl-8 pr-2.5 py-1.5 border border-borderColor focus:outline-none focus:border-accent"
            />
          </div>
        </div>

        {/* Member List */}
        <div className="space-y-2">
          {filteredMembers.map(member => (
            <div
              key={member.id || member.user_id}
              className="flex items-center justify-between p-2 rounded-xl bg-bgCard border border-borderColor hover:border-borderHover transition-colors"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="relative shrink-0">
                  <div className="w-8 h-8 rounded-full bg-bgTertiary text-textPrimary font-semibold text-xs flex items-center justify-center border border-borderMuted">
                    {member.full_name?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <div className="absolute bottom-0 right-0">
                    <OnlineBadge status={member.status} size="sm" />
                  </div>
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-medium text-textPrimary truncate">{member.full_name}</p>
                  <span className={`inline-block text-[9px] font-semibold px-1.5 py-0.5 rounded border capitalize ${getRoleBadgeColor(member.role)}`}>
                    {member.role}
                  </span>
                </div>
              </div>

              {/* Owner/Admin Action buttons */}
              {isOwnerOrAdmin && member.user_id !== currentUserId && (
                <div className="flex items-center space-x-1">
                  {onUpdateRole && (
                    <button
                      onClick={() => onUpdateRole(member.user_id, member.role === 'admin' ? 'member' : 'admin')}
                      className="p-1 hover:bg-bgHover text-textMuted hover:text-accentText rounded transition-colors"
                      title={member.role === 'admin' ? 'Demote to Member' : 'Promote to Admin'}
                    >
                      <Shield className="w-3.5 h-3.5" />
                    </button>
                  )}
                  {onRemoveMember && (
                    <button
                      onClick={() => onRemoveMember(member.user_id)}
                      className="p-1 hover:bg-bgHover text-textMuted hover:text-red-400 rounded transition-colors"
                      title="Remove Member"
                    >
                      <UserMinus className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Group Administration Footer Actions */}
        <div className="pt-4 border-t border-borderMuted space-y-2">
          {isOwnerOrAdmin && onArchiveGroup && (
            <button
              onClick={onArchiveGroup}
              className="w-full flex items-center justify-center space-x-2 py-2 px-3 bg-amber-500/10 hover:bg-amber-500/20 text-amber-500 border border-amber-500/30 rounded-xl text-xs font-semibold transition-all"
            >
              <Archive className="w-4 h-4" />
              <span>{conversation.is_archived ? 'Unarchive Group' : 'Archive Group'}</span>
            </button>
          )}

          {onRemoveMember && (
            <button
              onClick={() => setShowLeaveModal(true)}
              className="w-full flex items-center justify-center space-x-2 py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-xl text-xs font-semibold transition-all"
            >
              <LogOut className="w-4 h-4" />
              <span>Leave Group</span>
            </button>
          )}

          {/* Delete Group — Owner Only */}
          {isOwner && onDeleteGroup && (
            <div className="pt-2 border-t border-red-500/20">
              <button
                onClick={() => {
                  setDeleteConfirmName('');
                  setShowDeleteModal(true);
                }}
                className="w-full flex items-center justify-center space-x-2 py-2 px-3 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 rounded-xl text-xs font-semibold transition-all"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete Group</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Delete Group Safety Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-bgCard border border-red-500/30 rounded-2xl p-6 max-w-md w-full space-y-4 shadow-2xl animate-in fade-in zoom-in-95">
            <div className="flex items-center space-x-3 text-red-400">
              <div className="p-2.5 bg-red-500/10 rounded-xl border border-red-500/20">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold text-textPrimary text-base">Delete Group Permanently?</h3>
                <p className="text-xs text-textMuted">This action cannot be undone.</p>
              </div>
            </div>

            <div className="text-xs text-textSecondary leading-relaxed space-y-2 bg-bgInput p-3 rounded-xl border border-borderColor">
              <p>Are you sure you want to delete <strong className="text-textPrimary">"{conversation.name}"</strong>?</p>
              <ul className="list-disc pl-4 space-y-1 text-textMuted text-[11px]">
                <li>Group conversation and roster</li>
                <li>All direct message history and attachments</li>
                <li>Unread states and notifications</li>
              </ul>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-textMuted block">
                Type <span className="font-mono text-textPrimary font-semibold select-all">{conversation.name}</span> to confirm:
              </label>
              <input
                type="text"
                value={deleteConfirmName}
                onChange={e => setDeleteConfirmName(e.target.value)}
                placeholder="Enter group name..."
                className="w-full bg-bgInput text-textPrimary text-xs rounded-xl px-3 py-2.5 border border-borderColor focus:outline-none focus:border-red-500"
              />
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                onClick={() => setShowDeleteModal(false)}
                disabled={isDeleting}
                className="px-4 py-2 text-xs font-semibold text-textMuted hover:text-textPrimary rounded-xl transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={deleteConfirmName.trim() !== conversation.name || isDeleting}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold disabled:opacity-40 transition-all flex items-center space-x-1.5 shadow-lg shadow-red-900/30"
              >
                <Trash2 className="w-4 h-4" />
                <span>{isDeleting ? 'Deleting...' : 'Delete Permanently'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Leave Group Confirmation Modal */}
      {showLeaveModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-bgCard border border-borderColor rounded-2xl p-6 max-w-sm w-full space-y-4 shadow-2xl animate-in fade-in zoom-in-95">
            <div className="flex items-center space-x-3 text-amber-400">
              <div className="p-2.5 bg-amber-500/10 rounded-xl border border-amber-500/20">
                <LogOut className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold text-textPrimary text-base">Leave Group?</h3>
                <p className="text-xs text-textMuted">Confirm your departure</p>
              </div>
            </div>

            <p className="text-xs text-textSecondary leading-relaxed">
              You will no longer receive messages or updates from <strong className="text-textPrimary">"{conversation.name}"</strong>.
            </p>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                onClick={() => setShowLeaveModal(false)}
                disabled={isLeaving}
                className="px-4 py-2 text-xs font-semibold text-textMuted hover:text-textPrimary rounded-xl transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmLeave}
                disabled={isLeaving}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-bold disabled:opacity-50 transition-all flex items-center space-x-1.5"
              >
                <LogOut className="w-4 h-4" />
                <span>{isLeaving ? 'Leaving...' : 'Leave Group'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
