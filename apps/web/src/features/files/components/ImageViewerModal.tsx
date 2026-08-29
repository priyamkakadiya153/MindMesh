import React, { useState } from 'react';
import { AttachmentItem } from '../files-api';
import { X, Download, ZoomIn, ZoomOut, RotateCw, FileText, Info } from 'lucide-react';

interface ImageViewerModalProps {
  attachment: AttachmentItem | null;
  onClose: () => void;
}

export const ImageViewerModal: React.FC<ImageViewerModalProps> = ({ attachment, onClose }) => {
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [showDetails, setShowDetails] = useState(false);

  if (!attachment) return null;

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.5));
  const handleRotate = () => setRotation(prev => (prev + 90) % 360);

  return (
    <div className="fixed inset-0 bg-bgOverlay backdrop-blur-md z-50 flex flex-col justify-between">
      {/* Top Header Bar */}
      <div className="h-14 px-6 border-b border-borderMuted flex items-center justify-between bg-bgHeader">
        <div className="flex items-center space-x-3">
          <FileText className="w-5 h-5 text-emerald-400" />
          <div>
            <h3 className="text-xs font-semibold text-textPrimary">{attachment.original_filename}</h3>
            <p className="text-[10px] text-textMuted">Uploaded by {attachment.uploader_name || 'User'}</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button onClick={handleZoomOut} className="p-2 hover:bg-bgHover text-textMuted hover:text-textPrimary rounded-lg" title="Zoom Out">
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-xs text-textMuted font-mono">{Math.round(zoom * 100)}%</span>
          <button onClick={handleZoomIn} className="p-2 hover:bg-bgHover text-textMuted hover:text-textPrimary rounded-lg" title="Zoom In">
            <ZoomIn className="w-4 h-4" />
          </button>
          <button onClick={handleRotate} className="p-2 hover:bg-bgHover text-textMuted hover:text-textPrimary rounded-lg" title="Rotate">
            <RotateCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowDetails(prev => !prev)}
            className={`p-2 rounded-lg transition-colors ${showDetails ? 'bg-accentSubtle text-accentText' : 'hover:bg-bgHover text-textMuted'}`}
            title="Toggle File Info"
          >
            <Info className="w-4 h-4" />
          </button>
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

      {/* Main Image View */}
      <div className="flex-1 overflow-auto flex items-center justify-center p-6 relative">
        <div
          className="transition-transform duration-200 ease-out"
          style={{ transform: `scale(${zoom}) rotate(${rotation}deg)` }}
        >
          <img
            src={attachment.preview_url}
            alt={attachment.original_filename}
            className="max-h-[80vh] max-w-[80vw] object-contain shadow-2xl rounded-lg border border-borderColor"
          />
        </div>

        {/* Sidebar Info Drawer */}
        {showDetails && (
          <div className="absolute right-6 top-6 bottom-6 w-72 bg-bgDialog border border-borderColor rounded-2xl p-4 shadow-2xl flex flex-col space-y-4 text-xs select-none">
            <div className="flex items-center justify-between border-b border-borderMuted pb-2">
              <h4 className="font-semibold text-textPrimary">File Details</h4>
              <button onClick={() => setShowDetails(false)} className="text-textMuted hover:text-textPrimary">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-2 text-textSecondary">
              <div>
                <p className="text-[10px] text-textMuted font-medium">Filename</p>
                <p className="truncate font-mono">{attachment.original_filename}</p>
              </div>
              <div>
                <p className="text-[10px] text-textMuted font-medium">MIME Type</p>
                <p className="font-mono">{attachment.mime_type}</p>
              </div>
              <div>
                <p className="text-[10px] text-textMuted font-medium">File Size</p>
                <p>{(attachment.file_size / 1024).toFixed(1)} KB</p>
              </div>
              {attachment.checksum && (
                <div>
                  <p className="text-[10px] text-textMuted font-medium">SHA-256 Checksum</p>
                  <p className="font-mono text-[9px] break-all text-textMuted">{attachment.checksum}</p>
                </div>
              )}
              <div>
                <p className="text-[10px] text-textMuted font-medium">Total Downloads</p>
                <p>{attachment.download_count}</p>
              </div>
              <div>
                <p className="text-[10px] text-textMuted font-medium">Uploaded Date</p>
                <p>{new Date(attachment.created_at).toLocaleString()}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
