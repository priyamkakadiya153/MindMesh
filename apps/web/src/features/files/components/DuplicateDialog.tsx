import React from 'react';
import { AlertTriangle, Copy, GitCommit, X } from 'lucide-react';
import { DuplicateFileErrorPayload } from '../files-api';

interface DuplicateDialogProps {
  isOpen: boolean;
  duplicateInfo: DuplicateFileErrorPayload | null;
  onCancel: () => void;
  onReplaceVersion: () => void;
  onUploadCopy: () => void;
}

export function DuplicateDialog({
  isOpen,
  duplicateInfo,
  onCancel,
  onReplaceVersion,
  onUploadCopy
}: DuplicateDialogProps) {
  if (!isOpen || !duplicateInfo) return null;

  return (
    <div className="fixed inset-0 z-[60] bg-black/70 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-bgCard border border-amber-500/40 rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="p-4 bg-amber-500/10 border-b border-amber-500/20 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-textPrimary">Duplicate File Detected</h3>
              <p className="text-[11px] text-amber-400 font-medium">Matching SHA-256 hash found</p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="p-1 rounded-lg text-textMuted hover:text-textPrimary hover:bg-bgHover"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <p className="text-xs text-textSecondary leading-relaxed">
            An identical file named <span className="font-semibold text-textPrimary">&quot;{duplicateInfo.existing_filename}&quot;</span> already exists in your workspace.
          </p>

          <div className="p-3 bg-bgTertiary border border-borderColor rounded-xl space-y-1.5 text-[11px] text-textMuted">
            <div className="flex justify-between">
              <span>Existing File:</span>
              <span className="font-medium text-textPrimary truncate max-w-[200px]">{duplicateInfo.existing_filename}</span>
            </div>
            <div className="flex justify-between">
              <span>Uploaded By:</span>
              <span className="font-medium text-textPrimary">{duplicateInfo.uploaded_by}</span>
            </div>
            <div className="flex justify-between">
              <span>Date:</span>
              <span className="font-medium text-textPrimary">{new Date(duplicateInfo.created_at).toLocaleDateString()}</span>
            </div>
          </div>

          <p className="text-xs text-textMuted font-medium">How would you like to proceed?</p>

          <div className="space-y-2 pt-1">
            <button
              onClick={onReplaceVersion}
              className="w-full py-2.5 px-3.5 rounded-xl bg-accent hover:bg-accentHover text-white text-xs font-semibold flex items-center justify-center space-x-2 transition-all shadow-md"
            >
              <GitCommit className="w-4 h-4" />
              <span>Replace as New Version</span>
            </button>

            <button
              onClick={onUploadCopy}
              className="w-full py-2.5 px-3.5 rounded-xl border border-borderColor hover:bg-bgHover text-textPrimary text-xs font-semibold flex items-center justify-center space-x-2 transition-all"
            >
              <Copy className="w-4 h-4 text-purple-400" />
              <span>Upload as Separate Copy</span>
            </button>

            <button
              onClick={onCancel}
              className="w-full py-2 px-3.5 rounded-xl text-textMuted hover:text-textPrimary text-xs font-medium transition-colors"
            >
              Cancel Upload
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
