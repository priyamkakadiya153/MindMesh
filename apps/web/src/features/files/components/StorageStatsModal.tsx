import React, { useState, useEffect } from 'react';
import { X, HardDrive, FileText, Image as ImageIcon, FileCode, Film, Archive, Download, Eye, Loader2 } from 'lucide-react';
import { AttachmentItem, StorageStatsItem, getStorageStats } from '../files-api';

interface StorageStatsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPreviewItem: (item: AttachmentItem) => void;
  organizationId?: string;
  workspaceId?: string;
  token?: string;
}

export function StorageStatsModal({
  isOpen,
  onClose,
  onPreviewItem,
  organizationId,
  workspaceId,
  token
}: StorageStatsModalProps) {
  const [stats, setStats] = useState<StorageStatsItem | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsLoading(true);
      getStorageStats(organizationId, workspaceId, token)
        .then((data) => setStats(data))
        .catch((err) => console.error('Failed to load storage stats:', err))
        .finally(() => setIsLoading(false));
    }
  }, [isOpen, organizationId, workspaceId, token]);

  if (!isOpen) return null;

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  const getPercentage = (bytes: number, total: number) => {
    if (!total || total === 0) return 0;
    return Math.min(100, Math.round((bytes / total) * 100));
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-bgCard border border-borderColor rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-4 border-b border-borderColor flex items-center justify-between bg-bgSecondary">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-accentSubtle text-accentText">
              <HardDrive className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-textPrimary">Workspace Storage Analytics</h3>
              <p className="text-[11px] text-textMuted">Overview of storage quota and category distribution</p>
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
        <div className="p-5 flex-1 overflow-y-auto space-y-5">
          {isLoading || !stats ? (
            <div className="py-12 text-center text-xs text-textMuted flex items-center justify-center">
              <Loader2 className="w-4 h-4 animate-spin mr-2" /> Calculating storage distribution...
            </div>
          ) : (
            <>
              {/* Total Storage Summary Card */}
              <div className="p-4 rounded-2xl bg-bgTertiary border border-borderColor flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-textMuted uppercase tracking-wider">Total Storage Used</p>
                  <h2 className="text-2xl font-bold text-textPrimary mt-1">{formatSize(stats.total_bytes)}</h2>
                  <p className="text-[11px] text-textMuted mt-0.5">{stats.total_files} Active Files Indexed</p>
                </div>
                <div className="w-12 h-12 rounded-2xl bg-accentSubtle/50 text-accentText flex items-center justify-center">
                  <HardDrive className="w-6 h-6" />
                </div>
              </div>

              {/* Category Breakdown */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-textPrimary uppercase tracking-wider">Storage Breakdown by Category</h4>

                <div className="space-y-2.5">
                  {[
                    { label: 'Images', bytes: stats.by_category.images || 0, color: 'bg-emerald-400', icon: ImageIcon },
                    { label: 'Documents', bytes: stats.by_category.documents || 0, color: 'bg-rose-400', icon: FileText },
                    { label: 'Code', bytes: stats.by_category.code || 0, color: 'bg-purple-400', icon: FileCode },
                    { label: 'Media', bytes: stats.by_category.media || 0, color: 'bg-blue-400', icon: Film },
                    { label: 'Archives', bytes: stats.by_category.archives || 0, color: 'bg-amber-400', icon: Archive }
                  ].map((cat) => {
                    const pct = getPercentage(cat.bytes, stats.total_bytes);
                    const Icon = cat.icon;
                    return (
                      <div key={cat.label} className="p-3 bg-bgTertiary border border-borderColor rounded-xl space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-2">
                            <Icon className="w-4 h-4 text-textMuted" />
                            <span className="font-semibold text-textPrimary">{cat.label}</span>
                          </div>
                          <span className="text-textMuted font-mono">
                            {formatSize(cat.bytes)} ({pct}%)
                          </span>
                        </div>
                        <div className="w-full h-1.5 bg-bgInput rounded-full overflow-hidden">
                          <div className={`h-full ${cat.color} transition-all duration-300`} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Top 5 Largest Files */}
              {stats.largest_files.length > 0 && (
                <div className="space-y-2.5 pt-2">
                  <h4 className="text-xs font-bold text-textPrimary uppercase tracking-wider">Largest Files</h4>
                  <div className="space-y-2">
                    {stats.largest_files.map((file) => (
                      <div
                        key={file.id}
                        className="p-3 bg-bgCard border border-borderColor rounded-xl flex items-center justify-between text-xs"
                      >
                        <div className="min-w-0 flex-1 pr-3">
                          <p className="font-semibold text-textPrimary truncate">{file.original_filename}</p>
                          <p className="text-[10px] text-textMuted">
                            {formatSize(file.file_size)} • Uploaded by {file.uploader_name || 'User'}
                          </p>
                        </div>

                        <div className="flex items-center space-x-1 shrink-0">
                          <button
                            onClick={() => {
                              onClose();
                              onPreviewItem(file);
                            }}
                            className="p-1.5 hover:bg-bgHover text-textMuted hover:text-textPrimary rounded-lg"
                            title="Preview"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          <a
                            href={file.download_url}
                            download={file.original_filename}
                            className="p-1.5 hover:bg-bgHover text-textMuted hover:text-accentText rounded-lg"
                            title="Download"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
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
