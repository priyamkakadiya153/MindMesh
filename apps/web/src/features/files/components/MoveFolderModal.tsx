import React, { useState, useEffect } from 'react';
import { X, Folder, FolderPlus, Check, Loader2 } from 'lucide-react';
import { AttachmentItem, moveFile } from '../files-api';

interface MoveFolderModalProps {
  item: AttachmentItem | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (updated: AttachmentItem) => void;
  token?: string;
  workspaceId?: string;
}

interface FolderItem {
  id: string;
  name: string;
}

export function MoveFolderModal({ item, isOpen, onClose, onSuccess, token, workspaceId }: MoveFolderModalProps) {
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(item?.folder_id || null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);

  useEffect(() => {
    if (isOpen && workspaceId) {
      setIsLoading(true);
      fetch(`/api/v1/folders?workspace_id=${workspaceId}`, {
        headers: { Authorization: `Bearer ${token || localStorage.getItem('token') || ''}` }
      })
        .then((res) => (res.ok ? res.json() : []))
        .then((data) => setFolders(data))
        .catch((err) => console.error('Failed to load folders:', err))
        .finally(() => setIsLoading(false));
    }
  }, [isOpen, workspaceId, token]);

  useEffect(() => {
    if (item) {
      setSelectedFolderId(item.folder_id || null);
    }
  }, [item]);

  if (!isOpen || !item) return null;

  const handleCreateFolder = async () => {
    if (!newFolderName.trim() || !workspaceId) return;
    try {
      const res = await fetch('/api/v1/folders', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token || localStorage.getItem('token') || ''}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: newFolderName.trim(), workspace_id: workspaceId })
      });
      if (!res.ok) throw new Error('Failed to create folder');
      const created = await res.json();
      setFolders((prev) => [created, ...prev]);
      setSelectedFolderId(created.id);
      setNewFolderName('');
      setIsCreatingFolder(false);
    } catch (err: any) {
      alert(err.message || 'Error creating folder');
    }
  };

  const handleMove = async () => {
    try {
      setIsSubmitting(true);
      const updated = await moveFile(item.id, selectedFolderId, token);
      onSuccess(updated);
      onClose();
    } catch (err: any) {
      alert(err.message || 'Failed to move file');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-bgCard border border-borderColor rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-4 border-b border-borderColor flex items-center justify-between bg-bgSecondary">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-accentSubtle text-accentText">
              <Folder className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-textPrimary">Move File</h3>
              <p className="text-[11px] text-textMuted truncate max-w-[240px]">
                Select folder for &quot;{item.original_filename}&quot;
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

        {/* List of Folders */}
        <div className="p-4 space-y-3 max-h-72 overflow-y-auto">
          {/* Option for Workspace Root */}
          <div
            onClick={() => setSelectedFolderId(null)}
            className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
              selectedFolderId === null
                ? 'border-accent bg-accentSubtle/30 text-accentText font-semibold'
                : 'border-borderColor hover:border-borderHover bg-bgTertiary text-textPrimary'
            }`}
          >
            <div className="flex items-center space-x-2.5">
              <Folder className="w-4 h-4 text-accentText" />
              <span className="text-xs">Workspace Root (No Folder)</span>
            </div>
            {selectedFolderId === null && <Check className="w-4 h-4 text-accentText" />}
          </div>

          {isLoading ? (
            <div className="py-6 text-center text-xs text-textMuted flex items-center justify-center">
              <Loader2 className="w-4 h-4 animate-spin mr-2" /> Loading folders...
            </div>
          ) : (
            folders.map((folder) => (
              <div
                key={folder.id}
                onClick={() => setSelectedFolderId(folder.id)}
                className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                  selectedFolderId === folder.id
                    ? 'border-accent bg-accentSubtle/30 text-accentText font-semibold'
                    : 'border-borderColor hover:border-borderHover bg-bgTertiary text-textPrimary'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Folder className="w-4 h-4 text-amber-400" />
                  <span className="text-xs">{folder.name}</span>
                </div>
                {selectedFolderId === folder.id && <Check className="w-4 h-4 text-accentText" />}
              </div>
            ))
          )}

          {/* Create New Folder Inline */}
          {isCreatingFolder ? (
            <div className="p-3 bg-bgTertiary border border-borderColor rounded-xl space-y-2">
              <input
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                placeholder="New folder name..."
                className="w-full bg-bgInput text-textPrimary text-xs rounded-lg px-3 py-1.5 border border-borderColor focus:outline-none focus:border-accent"
                autoFocus
              />
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setIsCreatingFolder(false)}
                  className="px-3 py-1 rounded-lg text-[11px] text-textMuted hover:text-textPrimary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateFolder}
                  className="px-3 py-1 rounded-lg bg-accent text-white text-[11px] font-semibold"
                >
                  Create & Select
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setIsCreatingFolder(true)}
              className="w-full py-2 border border-dashed border-borderColor hover:border-accent rounded-xl text-xs text-textMuted hover:text-accentText flex items-center justify-center space-x-1.5 transition-colors"
            >
              <FolderPlus className="w-3.5 h-3.5" />
              <span>Create New Folder</span>
            </button>
          )}
        </div>

        {/* Footer */}
        <div className="p-3.5 border-t border-borderColor bg-bgSecondary flex items-center justify-end space-x-2">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl border border-borderColor text-textMuted hover:text-textPrimary text-xs font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleMove}
            disabled={isSubmitting}
            className="px-4 py-1.5 rounded-xl bg-accent hover:bg-accentHover text-white text-xs font-semibold flex items-center space-x-1 transition-colors"
          >
            {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />}
            <span>Move Here</span>
          </button>
        </div>
      </div>
    </div>
  );
}
