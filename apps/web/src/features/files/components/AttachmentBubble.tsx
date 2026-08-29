import React from 'react';
import { AttachmentItem } from '../files-api';
import { FileText, Image as ImageIcon, FileCode, Film, Archive, Download, Eye, ExternalLink } from 'lucide-react';

interface AttachmentBubbleProps {
  attachment: AttachmentItem;
  onPreview?: (attachment: AttachmentItem) => void;
}

export const AttachmentBubble: React.FC<AttachmentBubbleProps> = ({ attachment, onPreview }) => {
  const isImage = attachment.mime_type.startsWith('image/');
  const isPdf = attachment.mime_type.includes('pdf');
  const isCode = attachment.mime_type.includes('json') || attachment.mime_type.includes('javascript') || attachment.mime_type.includes('python');
  const isMedia = attachment.mime_type.startsWith('video/') || attachment.mime_type.startsWith('audio/');
  const isArchive = attachment.mime_type.includes('zip') || attachment.mime_type.includes('tar') || attachment.mime_type.includes('rar');

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = () => {
    if (isImage) return <ImageIcon className="w-5 h-5 text-emerald-400" />;
    if (isPdf) return <FileText className="w-5 h-5 text-rose-400" />;
    if (isCode) return <FileCode className="w-5 h-5 text-purple-400" />;
    if (isMedia) return <Film className="w-5 h-5 text-blue-400" />;
    if (isArchive) return <Archive className="w-5 h-5 text-amber-400" />;
    return <FileText className="w-5 h-5 text-slate-400" />;
  };

  return (
    <div className="mt-2 bg-bgCard border border-borderColor rounded-xl p-3 max-w-sm hover:border-borderHover transition-all group">
      {/* Thumbnail Preview for Images */}
      {isImage ? (
        <div
          onClick={() => onPreview && onPreview(attachment)}
          className="relative rounded-lg overflow-hidden mb-2 bg-bgTertiary aspect-video cursor-pointer border border-borderMuted group-hover:opacity-95 transition-opacity"
        >
          <img
            src={attachment.preview_url}
            alt={attachment.original_filename}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2">
            <span className="bg-bgDialog text-textPrimary text-[11px] px-2.5 py-1 rounded-lg font-medium flex items-center space-x-1">
              <Eye className="w-3.5 h-3.5" />
              <span>Preview</span>
            </span>
          </div>
        </div>
      ) : null}

      <div className="flex items-center justify-between space-x-3">
        <div className="flex items-center space-x-2.5 min-w-0">
          <div className="p-2 rounded-lg bg-bgTertiary border border-borderMuted shrink-0">
            {getFileIcon()}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-textPrimary truncate">{attachment.original_filename}</p>
            <p className="text-[10px] text-textMuted">{formatSize(attachment.file_size)}</p>
          </div>
        </div>

        <div className="flex items-center space-x-1 shrink-0">
          {onPreview && (
            <button
              onClick={() => onPreview(attachment)}
              className="p-1.5 hover:bg-bgHover text-textMuted hover:text-textPrimary rounded-lg transition-colors"
              title="Preview File"
            >
              <Eye className="w-4 h-4" />
            </button>
          )}
          <a
            href={attachment.download_url}
            download={attachment.original_filename}
            className="p-1.5 hover:bg-bgHover text-textMuted hover:text-accentText rounded-lg transition-colors"
            title="Download File"
          >
            <Download className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
};
