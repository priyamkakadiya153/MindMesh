import React from 'react';
import { AttachmentItem } from '../files-api';
import { X, Download, FileText, ExternalLink } from 'lucide-react';

interface PDFViewerModalProps {
  attachment: AttachmentItem | null;
  onClose: () => void;
}

export const PDFViewerModal: React.FC<PDFViewerModalProps> = ({ attachment, onClose }) => {
  if (!attachment) return null;

  return (
    <div className="fixed inset-0 bg-bgOverlay backdrop-blur-md z-50 flex flex-col justify-between">
      {/* Top Header */}
      <div className="h-14 px-6 border-b border-borderMuted flex items-center justify-between bg-bgHeader">
        <div className="flex items-center space-x-3">
          <FileText className="w-5 h-5 text-rose-500" />
          <div>
            <h3 className="text-xs font-semibold text-textPrimary">{attachment.original_filename}</h3>
            <p className="text-[10px] text-textMuted">{attachment.mime_type} • {(attachment.file_size / 1024).toFixed(1)} KB</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <a
            href={attachment.preview_url}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 hover:bg-bgHover text-textMuted hover:text-textPrimary rounded-lg"
            title="Open in new tab"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
          <a
            href={attachment.download_url}
            download={attachment.original_filename}
            className="px-3 py-1.5 bg-accent hover:bg-accentHover text-white text-xs font-semibold rounded-lg flex items-center space-x-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download</span>
          </a>
          <button onClick={onClose} className="p-2 hover:bg-bgHover text-textMuted hover:text-textPrimary rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Frame Container */}
      <div className="flex-1 p-4 bg-bgPrimary">
        <iframe
          src={attachment.preview_url}
          title={attachment.original_filename}
          className="w-full h-full rounded-xl border border-borderColor bg-white"
        />
      </div>
    </div>
  );
};
