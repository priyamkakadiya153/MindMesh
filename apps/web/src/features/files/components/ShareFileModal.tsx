import React, { useState, useEffect, useMemo } from 'react';
import {
  X,
  Share2,
  Users,
  Search,
  Check,
  Loader2,
  ShieldCheck,
  Trash2,
  Copy,
  CheckCircle2,
  AlertCircle,
  FileText,
  Lock,
  UserCheck
} from 'lucide-react';
import {
  AttachmentItem,
  ShareRecipientItem,
  shareFile,
  listFileShares,
  revokeFileShare
} from '../files-api';
import { getMembersDirectory } from '../../members/api';

interface ShareFileModalProps {
  isOpen: boolean;
  onClose: () => void;
  file: AttachmentItem | null;
  organizationId?: string;
  workspaceId?: string;
  token?: string;
  onShareUpdated?: () => void;
}

export function ShareFileModal({
  isOpen,
  onClose,
  file,
  organizationId,
  workspaceId,
  token,
  onShareUpdated
}: ShareFileModalProps) {
  const [members, setMembers] = useState<any[]>([]);
  const [isLoadingMembers, setIsLoadingMembers] = useState(false);
  const [existingShares, setExistingShares] = useState<ShareRecipientItem[]>([]);
  const [isLoadingShares, setIsLoadingShares] = useState(false);

  const [selectedMemberIds, setSelectedMemberIds] = useState<string[]>([]);
  const [customEmail, setCustomEmail] = useState('');
  const [permission, setPermission] = useState<'view' | 'edit' | 'admin'>('view');
  const [searchQuery, setSearchQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [copiedLink, setCopiedLink] = useState(false);

  // Load existing shares when modal opens with a file
  useEffect(() => {
    if (!isOpen || !file?.id) return;
    setSelectedMemberIds([]);
    setCustomEmail('');
    setError(null);
    setSuccessMessage(null);
    setCopiedLink(false);

    let isMounted = true;
    const fetchShares = async () => {
      try {
        setIsLoadingShares(true);
        const shares = await listFileShares(file.id, token);
        if (isMounted) setExistingShares(shares);
      } catch (err: any) {
        console.error('Failed to load file shares:', err);
      } finally {
        if (isMounted) setIsLoadingShares(false);
      }
    };

    fetchShares();
    return () => {
      isMounted = false;
    };
  }, [isOpen, file?.id, token]);

  // Load org/workspace members directory
  useEffect(() => {
    if (!isOpen || !organizationId) return;
    let isMounted = true;

    const fetchMembers = async () => {
      try {
        setIsLoadingMembers(true);
        const data = await getMembersDirectory(
          token || localStorage.getItem('token') || '',
          organizationId,
          workspaceId
        );
        if (isMounted) {
          const list = Array.isArray(data) ? data : data.members || [];
          setMembers(list);
        }
      } catch (err: any) {
        console.error('Failed to load directory members:', err);
      } finally {
        if (isMounted) setIsLoadingMembers(false);
      }
    };

    fetchMembers();
    return () => {
      isMounted = false;
    };
  }, [isOpen, organizationId, workspaceId, token]);

  // Filter members excluding current uploader
  const filteredMembers = useMemo(() => {
    return members.filter((m) => {
      const uId = m.user_id || m.user?.id || m.id || '';
      if (file && file.uploaded_by === uId) return false; // don't list uploader as target to share
      const email = (m.email || m.user?.email || '').toLowerCase();
      const name = (m.username || (m.user?.first_name ? `${m.user.first_name} ${m.user.last_name || ''}` : '') || '').toLowerCase();
      const q = searchQuery.toLowerCase().trim();
      if (!q) return true;
      return email.includes(q) || name.includes(q);
    });
  }, [members, file, searchQuery]);

  if (!isOpen || !file) return null;

  const toggleMember = (userId: string) => {
    setSelectedMemberIds((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleShareSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file?.id) return;

    const emails = customEmail.trim() ? [customEmail.trim()] : [];
    if (selectedMemberIds.length === 0 && emails.length === 0) {
      setError('Please select at least one team member or enter an email address.');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const res = await shareFile(
        file.id,
        {
          recipient_user_ids: selectedMemberIds,
          recipient_emails: emails,
          permission
        },
        token
      );

      const count = res.shared_count ?? selectedMemberIds.length;
      setSuccessMessage(res.message || `File successfully shared with ${count} member(s).`);
      setSelectedMemberIds([]);
      setCustomEmail('');

      // Refresh share list
      const updatedShares = await listFileShares(file.id, token);
      setExistingShares(updatedShares);
      if (onShareUpdated) onShareUpdated();
    } catch (err: any) {
      setError(err.message || 'Failed to share file. Please verify permissions.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRevokeShare = async (recipientUserId: string) => {
    if (!file?.id) return;
    try {
      await revokeFileShare(file.id, recipientUserId, token);
      setExistingShares((prev) => prev.filter((s) => s.shared_with !== recipientUserId && s.user_id !== recipientUserId));
      setSuccessMessage('Share access revoked.');
      if (onShareUpdated) onShareUpdated();
    } catch (err: any) {
      setError(err.message || 'Failed to revoke file share');
    }
  };

  const handleCopyLink = () => {
    const shareUrl = `${window.location.origin}/files?sharing_filter=shared_with_me&file_id=${file.id}`;
    navigator.clipboard.writeText(shareUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 3000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-bgCard border border-borderColor rounded-2xl w-full max-w-lg shadow-2xl flex flex-col max-h-[90vh] overflow-hidden animate-in fade-in zoom-in-95 duration-150 text-textPrimary">
        {/* Header */}
        <div className="p-4 border-b border-borderColor flex items-center justify-between bg-bgSecondary">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-accentSubtle text-accentText">
              <Share2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-textPrimary flex items-center space-x-1.5">
                <span>Share File</span>
              </h3>
              <p className="text-[11px] text-textMuted mt-0.5 truncate max-w-xs font-mono">
                {file.original_filename}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl hover:bg-bgHover text-textMuted hover:text-textPrimary transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-4 overflow-y-auto space-y-4 text-xs">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMessage && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          <form onSubmit={handleShareSubmit} className="space-y-4">
            {/* Permission and Quick Add */}
            <div>
              <label className="block text-xs font-medium text-textSecondary mb-1.5">
                Share with Workspace Members
              </label>

              {/* Search Member */}
              <div className="relative mb-2">
                <Search className="w-3.5 h-3.5 text-textMuted absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search members by name or email..."
                  className="w-full bg-bgInput text-textPrimary placeholder-textMuted text-xs rounded-xl pl-9 pr-3 py-2 border border-borderColor focus:outline-none focus:border-accent"
                />
              </div>

              {/* Members List Container */}
              <div className="max-h-40 overflow-y-auto space-y-1 p-2 bg-bgTertiary border border-borderMuted rounded-xl">
                {isLoadingMembers ? (
                  <div className="p-4 text-center text-textMuted text-xs flex items-center justify-center space-x-2">
                    <Loader2 className="w-4 h-4 animate-spin text-accentText" />
                    <span>Loading members directory...</span>
                  </div>
                ) : filteredMembers.length === 0 ? (
                  <div className="p-3 text-center text-textMuted text-xs">
                    {searchQuery ? `No members matching "${searchQuery}".` : 'No other workspace members found.'}
                  </div>
                ) : (
                  filteredMembers.map((m) => {
                    const uId = m.user_id || m.id || m.user?.id || '';
                    const uEmail = m.email || m.user?.email || '';
                    const uName = m.full_name || m.display_name || m.username || (m.first_name ? `${m.first_name} ${m.last_name || ''}`.trim() : '') || uEmail;
                    const isSelected = selectedMemberIds.includes(uId);
                    const isAlreadyShared = existingShares.some((s) => s.shared_with === uId || s.user_id === uId);

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
                            {(uName || 'M').charAt(0).toUpperCase()}
                          </div>
                          <div className="min-w-0 text-left">
                            <p className="font-semibold text-textPrimary truncate text-xs">{uName}</p>
                            <p className="text-[10px] text-textMuted truncate">{uEmail}</p>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 shrink-0">
                          {isAlreadyShared && (
                            <span className="text-[9px] font-medium px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              Shared
                            </span>
                          )}
                          <div
                            className={`w-4 h-4 rounded flex items-center justify-center border ${
                              isSelected
                                ? 'bg-accent border-accent text-white'
                                : 'border-borderColor bg-bgInput'
                            }`}
                          >
                            {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Direct Email Write-In */}
            <div>
              <label className="block text-[11px] font-medium text-textSecondary mb-1">
                Or invite by email address:
              </label>
              <input
                type="email"
                value={customEmail}
                onChange={(e) => setCustomEmail(e.target.value)}
                placeholder="colleague@company.com"
                className="w-full bg-bgInput text-textPrimary placeholder-textMuted text-xs rounded-xl px-3 py-2 border border-borderColor focus:outline-none focus:border-accent"
              />
            </div>

            {/* Permission Dropdown */}
            <div className="flex items-center justify-between pt-1">
              <span className="text-xs font-medium text-textSecondary">Access Level:</span>
              <select
                value={permission}
                onChange={(e) => setPermission(e.target.value as any)}
                className="bg-bgInput text-textPrimary text-xs rounded-xl px-2.5 py-1.5 border border-borderColor focus:outline-none focus:border-accent"
              >
                <option value="view">Can view & download</option>
                <option value="edit">Can edit & version</option>
                <option value="admin">Full access</option>
              </select>
            </div>

            {/* Share Submit Button */}
            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="submit"
                disabled={isSubmitting || (selectedMemberIds.length === 0 && !customEmail.trim())}
                className="w-full py-2 bg-accent hover:bg-accentHover disabled:opacity-50 disabled:hover:bg-accent text-white rounded-xl text-xs font-semibold shadow-lg shadow-accent/20 transition-all flex items-center justify-center space-x-1.5"
              >
                {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Share2 className="w-4 h-4" />}
                <span>
                  Share File {selectedMemberIds.length > 0 ? `(${selectedMemberIds.length} selected)` : ''}
                </span>
              </button>
            </div>
          </form>

          {/* Active Share Recipients Section */}
          <div className="pt-3 border-t border-borderColor space-y-2">
            <h4 className="text-xs font-semibold text-textPrimary flex items-center justify-between">
              <span>Who Has Access ({existingShares.length})</span>
              <button
                type="button"
                onClick={handleCopyLink}
                className="text-[11px] text-accentText hover:underline font-medium flex items-center space-x-1"
              >
                {copiedLink ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-400" />
                    <span className="text-emerald-400">Link Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>Copy Share Link</span>
                  </>
                )}
              </button>
            </h4>

            {isLoadingShares ? (
              <div className="p-3 text-center text-textMuted text-xs flex items-center justify-center space-x-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-accentText" />
                <span>Loading access list...</span>
              </div>
            ) : existingShares.length === 0 ? (
              <p className="text-[11px] text-textMuted italic py-1">
                No direct recipient shares created yet.
              </p>
            ) : (
              <div className="space-y-1.5 max-h-36 overflow-y-auto">
                {existingShares.map((s) => {
                  const name = s.recipient_name || s.recipient_email || 'Member';
                  const email = s.recipient_email || '';
                  const permLabel =
                    s.permission === 'admin'
                      ? 'Full access'
                      : s.permission === 'edit'
                      ? 'Can edit & version'
                      : 'Can view & download';
                  const recipientId = s.shared_with || s.user_id || s.id;

                  return (
                    <div
                      key={s.id}
                      className="p-2.5 bg-bgTertiary border border-borderMuted rounded-xl flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center space-x-2.5 min-w-0 pr-2">
                        <div className="w-7 h-7 rounded-full bg-accent/10 border border-accent/30 text-accent font-semibold text-xs flex items-center justify-center shrink-0">
                          {(name || 'M').charAt(0).toUpperCase()}
                        </div>
                        <div className="min-w-0 text-left">
                          <p className="font-semibold text-textPrimary truncate">{name}</p>
                          <p className="text-[10px] text-textMuted truncate">
                            {email ? `${email} • ` : ''}
                            <span className="font-medium text-textSecondary">{permLabel}</span>
                          </p>
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => handleRevokeShare(recipientId)}
                        className="p-1.5 text-textMuted hover:text-rose-400 hover:bg-bgHover rounded-lg transition-colors"
                        title="Revoke Access"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-3.5 border-t border-borderColor bg-bgSecondary flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-bgTertiary hover:bg-bgHover border border-borderMuted text-textPrimary text-xs font-semibold transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
