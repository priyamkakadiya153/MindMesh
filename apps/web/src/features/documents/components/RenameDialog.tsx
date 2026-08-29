import React, { useState, useEffect } from 'react';
import { X, Edit2, Loader2 } from 'lucide-react';
import { Document } from '../types';

interface RenameDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (newTitle: string) => Promise<void>;
  document: Document | null;
}

export const RenameDialog: React.FC<RenameDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  document
}) => {
  const [title, setTitle] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (document) {
      setTitle(document.title || document.filename || '');
      setError(null);
    }
  }, [document, isOpen]);

  if (!isOpen || !document) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Document title cannot be empty.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onConfirm(title.trim());
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to rename document.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
      <div className="w-full max-w-md bg-bgDialog border border-borderColor p-5 rounded-2xl shadow-2xl font-outfit text-textPrimary space-y-4">
        <div className="flex items-center justify-between border-b border-borderMuted pb-3">
          <div className="flex items-center gap-2">
            <Edit2 className="w-4 h-4 text-accent" />
            <h3 className="text-sm font-bold tracking-tight">Rename Document</h3>
          </div>
          <button
            onClick={onClose}
            className="text-textMuted hover:text-textPrimary p-1 rounded-lg hover:bg-bgHover transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="rename-input" className="block text-xs font-medium text-textMuted mb-1">
              Document Name / Title
            </label>
            <input
              id="rename-input"
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-bgInput border border-borderColor rounded-xl px-3 py-2 text-xs text-textPrimary outline-none focus:border-accent focus:ring-1 focus:ring-accent"
              placeholder="Enter new filename..."
            />
          </div>

          {error && (
            <p className="text-xs text-dangerText font-medium bg-dangerBg border border-dangerBorder p-2 rounded-xl">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-textMuted hover:text-textPrimary border border-borderColor rounded-xl hover:bg-bgHover transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 text-xs font-semibold text-white bg-accent hover:bg-accentHover rounded-xl transition flex items-center gap-1.5 disabled:opacity-50"
            >
              {saving ? <Loader2 size={13} className="animate-spin" /> : null}
              <span>Save Changes</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
export default RenameDialog;
