import React from 'react';
import { Package, Download, HardDrive, Calendar, User, CheckCircle, Loader2 } from 'lucide-react';
import { AttachmentItem } from '../files-api';

interface GenericFilePreviewProps {
  item: AttachmentItem;
  categoryLabel: string;
  onDownload: () => void;
  isDownloading: boolean;
}

export function GenericFilePreview({ item, categoryLabel, onDownload, isDownloading }: GenericFilePreviewProps) {
  const filename = item.original_filename || 'file';
  const ext = filename.split('.').pop()?.toUpperCase() || 'BINARY';

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="max-w-md w-full bg-bgCard border border-borderColor rounded-2xl p-8 text-center shadow-xl animate-in fade-in duration-200">
      <div className="w-20 h-20 rounded-3xl bg-accentSubtle border border-accent/30 text-accentText flex items-center justify-center mx-auto mb-4 shadow-sm">
        <Package className="w-10 h-10" />
      </div>

      <h4 className="text-base font-bold text-textPrimary mb-1 truncate" title={filename}>{filename}</h4>
      <p className="text-xs font-semibold text-accentText mb-3">{categoryLabel}</p>

      <p className="text-xs text-textMuted mb-6 leading-relaxed">
        MindMesh can safely store and deliver this file, but no visual renderer is available yet for <span className="font-semibold text-textPrimary">.{ext}</span> files.
      </p>

      <div className="bg-bgTertiary border border-borderColor rounded-xl p-4 text-left space-y-2.5 text-xs mb-6">
        <div className="flex items-center justify-between text-textMuted">
          <span className="flex items-center"><HardDrive className="w-3.5 h-3.5 mr-2 text-accentText" /> Size:</span>
          <span className="font-semibold text-textPrimary font-mono">{formatSize(item.file_size)}</span>
        </div>
        {item.uploader_name && (
          <div className="flex items-center justify-between text-textMuted">
            <span className="flex items-center"><User className="w-3.5 h-3.5 mr-2 text-purple-400" /> Uploaded by:</span>
            <span className="font-semibold text-textPrimary">{item.uploader_name}</span>
          </div>
        )}
        {item.created_at && (
          <div className="flex items-center justify-between text-textMuted">
            <span className="flex items-center"><Calendar className="w-3.5 h-3.5 mr-2 text-emerald-400" /> Date:</span>
            <span className="font-semibold text-textPrimary">{new Date(item.created_at).toLocaleString()}</span>
          </div>
        )}
        <div className="flex items-center justify-between text-textMuted">
          <span className="flex items-center"><CheckCircle className="w-3.5 h-3.5 mr-2 text-blue-400" /> Storage Status:</span>
          <span className="font-semibold text-emerald-400">Safely Stored & Ready</span>
        </div>
      </div>

      <button
        type="button"
        onClick={onDownload}
        disabled={isDownloading}
        aria-label="Download File"
        className="w-full py-2.5 rounded-xl bg-accent hover:bg-accentHover disabled:opacity-50 text-white text-xs font-semibold flex items-center justify-center space-x-2 transition-all shadow-md cursor-pointer"
      >
        {isDownloading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Downloading...</span>
          </>
        ) : (
          <>
            <Download className="w-4 h-4" />
            <span>Download File ({ext})</span>
          </>
        )}
      </button>
    </div>
  );
}
