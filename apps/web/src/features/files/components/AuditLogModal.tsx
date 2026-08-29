import React, { useState, useEffect } from 'react';
import { X, ShieldCheck, Download, Eye, Upload, Edit2, Folder, Trash2, RotateCcw, Loader2 } from 'lucide-react';
import { AttachmentItem, AttachmentAuditLogItem, getFileAuditLogs } from '../files-api';

interface AuditLogModalProps {
  item: AttachmentItem | null;
  isOpen: boolean;
  onClose: () => void;
  token?: string;
}

export function AuditLogModal({ item, isOpen, onClose, token }: AuditLogModalProps) {
  const [logs, setLogs] = useState<AttachmentAuditLogItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen && item) {
      setIsLoading(true);
      getFileAuditLogs(item.id, token)
        .then((data) => setLogs(data))
        .catch((err) => console.error('Failed to load audit logs:', err))
        .finally(() => setIsLoading(false));
    }
  }, [isOpen, item, token]);

  if (!isOpen || !item) return null;

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'upload':
      case 'version_upload':
        return <Upload className="w-3.5 h-3.5 text-emerald-400" />;
      case 'download':
      case 'version_download':
        return <Download className="w-3.5 h-3.5 text-blue-400" />;
      case 'preview':
        return <Eye className="w-3.5 h-3.5 text-purple-400" />;
      case 'rename':
        return <Edit2 className="w-3.5 h-3.5 text-amber-400" />;
      case 'move':
        return <Folder className="w-3.5 h-3.5 text-indigo-400" />;
      case 'delete':
        return <Trash2 className="w-3.5 h-3.5 text-rose-400" />;
      case 'restore':
      case 'version_restore':
        return <RotateCcw className="w-3.5 h-3.5 text-teal-400" />;
      default:
        return <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-bgCard border border-borderColor rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-4 border-b border-borderColor flex items-center justify-between bg-bgSecondary">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-blue-500/20 text-blue-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-textPrimary">Security Audit Trail</h3>
              <p className="text-[11px] text-textMuted truncate max-w-[260px]">
                {item.original_filename}
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
        <div className="p-4 flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="py-12 text-center text-xs text-textMuted flex items-center justify-center">
              <Loader2 className="w-4 h-4 animate-spin mr-2" /> Loading audit history...
            </div>
          ) : logs.length === 0 ? (
            <div className="py-12 text-center text-xs text-textMuted">No recorded audit logs yet.</div>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="p-3 bg-bgTertiary border border-borderColor rounded-xl flex items-center justify-between text-xs"
                >
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-bgCard border border-borderColor shrink-0">
                      {getActionIcon(log.action)}
                    </div>
                    <div>
                      <p className="font-semibold text-textPrimary capitalize">
                        {log.action.replace('_', ' ')}
                      </p>
                      <p className="text-[11px] text-textMuted mt-0.5">
                        By <span className="text-textPrimary">{log.user_name || 'User'}</span>
                        {log.ip_address && ` • IP ${log.ip_address}`}
                      </p>
                    </div>
                  </div>

                  <span className="text-[10px] text-textMuted shrink-0">
                    {new Date(log.accessed_at).toLocaleString()}
                  </span>
                </div>
              ))}
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
