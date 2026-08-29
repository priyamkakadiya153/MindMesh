import React, { useState, useEffect, useRef } from 'react';
import { X, GitBranch, Download, RotateCcw, Upload, Loader2, CheckCircle2 } from 'lucide-react';
import {
  AttachmentItem,
  AttachmentVersionItem,
  listFileVersions,
  uploadFileVersion,
  restoreFileVersion
} from '../files-api';

interface VersionHistoryModalProps {
  item: AttachmentItem | null;
  isOpen: boolean;
  onClose: () => void;
  onVersionChanged: (updatedItem: AttachmentItem) => void;
  token?: string;
}

export function VersionHistoryModal({
  item,
  isOpen,
  onClose,
  onVersionChanged,
  token
}: VersionHistoryModalProps) {
  const [versions, setVersions] = useState<AttachmentVersionItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [restoringVersion, setRestoringVersion] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen && item) {
      setIsLoading(true);
      listFileVersions(item.id, token)
        .then((data) => setVersions(data))
        .catch((err) => console.error('Failed to load version history:', err))
        .finally(() => setIsLoading(false));
    }
  }, [isOpen, item, token]);

  if (!isOpen || !item) return null;

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleUploadNewVersion = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setIsUploading(true);
      const updated = await uploadFileVersion(item.id, file, token);
      onVersionChanged(updated);
      const refreshed = await listFileVersions(item.id, token);
      setVersions(refreshed);
    } catch (err: any) {
      alert(err.message || 'Failed to upload new version');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleRestore = async (versionNumber: number) => {
    if (confirm(`Restore version v${versionNumber} as current active file?`)) {
      try {
        setRestoringVersion(versionNumber);
        const updated = await restoreFileVersion(item.id, versionNumber, token);
        onVersionChanged(updated);
        const refreshed = await listFileVersions(item.id, token);
        setVersions(refreshed);
      } catch (err: any) {
        alert(err.message || 'Failed to restore version');
      } finally {
        setRestoringVersion(null);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-bgCard border border-borderColor rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-4 border-b border-borderColor flex items-center justify-between bg-bgSecondary">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400">
              <GitBranch className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-textPrimary">Version History</h3>
              <p className="text-[11px] text-textMuted truncate max-w-[260px]">
                {item.original_filename} (Current: v{item.version})
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

        {/* Content Body */}
        <div className="p-4 flex-1 overflow-y-auto space-y-3">
          <div className="flex items-center justify-between bg-bgTertiary p-3 rounded-xl border border-borderColor">
            <div>
              <p className="text-xs font-semibold text-textPrimary">Upload New Version</p>
              <p className="text-[11px] text-textMuted">Replace current content with a new revision</p>
            </div>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleUploadNewVersion}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="px-3 py-1.5 rounded-xl bg-accent hover:bg-accentHover text-white text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-sm shrink-0"
            >
              {isUploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
              <span>Upload New File</span>
            </button>
          </div>

          {isLoading ? (
            <div className="py-8 text-center text-xs text-textMuted flex items-center justify-center">
              <Loader2 className="w-4 h-4 animate-spin mr-2" /> Loading version timeline...
            </div>
          ) : (
            <div className="space-y-2">
              {versions.map((ver) => {
                const isCurrent = ver.version_number === item.version;
                return (
                  <div
                    key={ver.id}
                    className={`p-3.5 rounded-xl border flex items-center justify-between transition-all ${
                      isCurrent
                        ? 'border-accent bg-accentSubtle/20'
                        : 'border-borderColor bg-bgCard hover:border-borderHover'
                    }`}
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <div
                        className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold ${
                          isCurrent ? 'bg-accent text-white' : 'bg-bgTertiary text-textMuted'
                        }`}
                      >
                        v{ver.version_number}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-semibold text-textPrimary">
                            Version {ver.version_number}
                          </span>
                          {isCurrent && (
                            <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400 text-[10px] font-bold flex items-center space-x-1">
                              <CheckCircle2 className="w-3 h-3 mr-1" /> Current
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-textMuted mt-0.5">
                          {formatSize(ver.file_size)} • {ver.creator_name || 'User'} •{' '}
                          {new Date(ver.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-1 shrink-0">
                      <a
                        href={`/api/v1/files/${item.id}/versions/${ver.version_number}/download`}
                        download
                        className="p-1.5 rounded-lg hover:bg-bgHover text-textMuted hover:text-accentText transition-colors"
                        title="Download this version"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                      {!isCurrent && (
                        <button
                          onClick={() => handleRestore(ver.version_number)}
                          disabled={restoringVersion === ver.version_number}
                          className="p-1.5 rounded-lg hover:bg-bgHover text-textMuted hover:text-purple-400 transition-colors"
                          title="Restore this version"
                        >
                          {restoringVersion === ver.version_number ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <RotateCcw className="w-4 h-4" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-borderColor bg-bgSecondary flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl border border-borderColor text-textMuted hover:text-textPrimary text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
