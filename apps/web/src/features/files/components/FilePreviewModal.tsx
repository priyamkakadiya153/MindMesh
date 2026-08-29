import React, { useState, useEffect, useRef } from 'react';
import { X, Download, FileText, FileCode, Eye, Calendar, User, Loader2, RotateCw, Scissors, Package, Film, Archive, Sparkles } from 'lucide-react';
import { AttachmentItem } from '../files-api';
import { detectFileType } from '../utils/fileCapabilities';
import { EmbroideryPreview } from './EmbroideryPreview';
import { GenericFilePreview } from './GenericFilePreview';
import { FileIntelligenceCard } from './FileIntelligenceCard';

interface FilePreviewModalProps {
  item: AttachmentItem | null;
  onClose: () => void;
}

export function FilePreviewModal({ item, onClose }: FilePreviewModalProps) {
  const [textContent, setTextContent] = useState<string | null>(null);
  const [isLoadingText, setIsLoadingText] = useState(false);
  const [textError, setTextError] = useState<string | null>(null);

  const [pdfObjectUrl, setPdfObjectUrl] = useState<string | null>(null);
  const [isLoadingPdf, setIsLoadingPdf] = useState(false);
  const [pdfError, setPdfError] = useState(false);

  const [imageObjectUrl, setImageObjectUrl] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const backdropRef = useRef<HTMLDivElement>(null);

  const filename = item?.original_filename || '';
  const mime = item?.mime_type || '';
  const caps = detectFileType(filename, mime);

  const isPdf = caps.previewType === 'pdf';
  const isImage = caps.previewType === 'image';
  const isCodeOrText = caps.previewType === 'text' || caps.previewType === 'code';
  const isEmbroidery = caps.previewType === 'embroidery';
  const isGeneric = caps.previewType === 'generic';

  // Global keyboard ESC key listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Load PDF Blob
  useEffect(() => {
    let active = true;
    let createdUrl: string | null = null;

    if (item && isPdf) {
      setIsLoadingPdf(true);
      setPdfError(false);
      const token = localStorage.getItem('token') || '';
      const headers: HeadersInit = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const previewUrlWithToken = token ? `${item.preview_url}?token=${encodeURIComponent(token)}` : item.preview_url;

      fetch(previewUrlWithToken, { headers })
        .then(async (res) => {
          if (!res.ok) throw new Error('PDF Preview fetch failed');
          const blob = await res.blob();
          if (!active) return;
          const pdfBlob = new Blob([blob], { type: 'application/pdf' });
          createdUrl = URL.createObjectURL(pdfBlob);
          setPdfObjectUrl(createdUrl);
        })
        .catch((err) => {
          console.error('PDF preview error:', err);
          if (active) setPdfError(true);
        })
        .finally(() => {
          if (active) setIsLoadingPdf(false);
        });
    } else {
      setPdfObjectUrl(null);
    }

    return () => {
      active = false;
      if (createdUrl) {
        URL.revokeObjectURL(createdUrl);
      }
    };
  }, [item?.id, isPdf]);

  // Load Image Blob
  useEffect(() => {
    let active = true;
    let createdUrl: string | null = null;

    if (item && isImage) {
      const token = localStorage.getItem('token') || '';
      const headers: HeadersInit = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const previewUrlWithToken = token ? `${item.preview_url}?token=${encodeURIComponent(token)}` : item.preview_url;

      fetch(previewUrlWithToken, { headers })
        .then(async (res) => {
          if (!res.ok) throw new Error('Image fetch failed');
          const blob = await res.blob();
          if (!active) return;
          createdUrl = URL.createObjectURL(blob);
          setImageObjectUrl(createdUrl);
        })
        .catch(() => {
          if (active) setImageObjectUrl(item.preview_url);
        });
    } else {
      setImageObjectUrl(null);
    }

    return () => {
      active = false;
      if (createdUrl) {
        URL.revokeObjectURL(createdUrl);
      }
    };
  }, [item?.id, isImage]);

  // Load Text Content
  const loadTextContent = () => {
    if (item && isCodeOrText) {
      setIsLoadingText(true);
      setTextError(null);
      const token = localStorage.getItem('token') || '';
      const headers: HeadersInit = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const previewUrlWithToken = token ? `${item.preview_url}?token=${encodeURIComponent(token)}` : item.preview_url;

      fetch(previewUrlWithToken, { headers })
        .then((res) => {
          if (!res.ok) throw new Error('Failed to load text preview');
          return res.text();
        })
        .then((data) => {
          setTextContent(data);
        })
        .catch((err) => {
          setTextError(err.message || 'Unable to preview this file.');
        })
        .finally(() => {
          setIsLoadingText(false);
        });
    } else {
      setTextContent(null);
    }
  };

  useEffect(() => {
    loadTextContent();
  }, [item?.id, isCodeOrText]);

  if (!item) return null;

  const handleDownload = async () => {
    if (isDownloading || !item) return;
    setIsDownloading(true);
    try {
      const token = localStorage.getItem('token') || '';
      const downloadUrlWithToken = token ? `${item.download_url}?token=${encodeURIComponent(token)}` : item.download_url;
      const res = await fetch(downloadUrlWithToken);
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download error:', err);
      alert('Unable to download the file. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === backdropRef.current) {
      onClose();
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getHeaderIcon = () => {
    switch (caps.iconType) {
      case 'embroidery': return <Scissors className="w-5 h-5 text-purple-400" />;
      case 'image': return <Eye className="w-5 h-5 text-emerald-400" />;
      case 'pdf': return <FileText className="w-5 h-5 text-rose-400" />;
      case 'code': return <FileCode className="w-5 h-5 text-purple-400" />;
      case 'text': return <FileText className="w-5 h-5 text-blue-400" />;
      case 'video': return <Film className="w-5 h-5 text-indigo-400" />;
      case 'archive': return <Archive className="w-5 h-5 text-amber-400" />;
      default: return <Package className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div
      ref={backdropRef}
      onClick={handleBackdropClick}
      aria-label="Preview file modal"
      className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 animate-in fade-in duration-200"
    >
      <div className="bg-bgCard border border-borderColor rounded-2xl w-full max-w-5xl shadow-2xl flex flex-col h-[88vh] overflow-hidden relative">
        {/* Header */}
        <div className="p-3.5 sm:p-4 border-b border-borderColor flex items-center justify-between bg-bgSecondary">
          <div className="flex items-center space-x-3 min-w-0">
            <div className="p-2 rounded-xl bg-accentSubtle text-accentText shrink-0">
              {getHeaderIcon()}
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-textPrimary truncate" title={filename}>{filename}</h3>
              <p className="text-[11px] text-textMuted flex items-center space-x-2 mt-0.5">
                <span>{formatSize(item.file_size)}</span>
                <span>•</span>
                <span>{caps.categoryLabel}</span>
                {item.uploader_name && (
                  <>
                    <span>•</span>
                    <span>Uploaded by {item.uploader_name}</span>
                  </>
                )}
                {item.created_at && (
                  <>
                    <span>•</span>
                    <span>{new Date(item.created_at).toLocaleDateString()}</span>
                  </>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <button
              type="button"
              onClick={handleDownload}
              disabled={isDownloading}
              aria-label="Download file"
              className="px-3 py-1.5 rounded-xl bg-accent hover:bg-accentHover disabled:opacity-50 text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-sm cursor-pointer"
            >
              {isDownloading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Downloading...</span>
                </>
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  <span>Download</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={onClose}
              aria-label="Close file preview"
              className="p-1.5 rounded-xl hover:bg-bgHover text-textMuted hover:text-textPrimary transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Body Router */}
        <div className="flex-1 bg-bgTertiary/30 overflow-auto p-4 flex items-center justify-center">
          {isEmbroidery ? (
            <EmbroideryPreview
              item={item}
              onDownload={handleDownload}
              isDownloading={isDownloading}
            />
          ) : isImage ? (
            <div className="max-w-full max-h-full flex flex-col items-center justify-center">
              <img
                src={imageObjectUrl || item.preview_url}
                alt={filename}
                className="max-h-[70vh] max-w-full object-contain rounded-xl border border-borderColor shadow-lg"
              />
            </div>
          ) : isPdf ? (
            isLoadingPdf ? (
              <div className="flex flex-col items-center justify-center h-full text-textMuted space-y-2">
                <Loader2 className="w-6 h-6 animate-spin text-rose-400" />
                <span className="text-xs font-medium">Rendering PDF document...</span>
              </div>
            ) : pdfError || !pdfObjectUrl ? (
              <GenericFilePreview
                item={item}
                categoryLabel="PDF Document"
                onDownload={handleDownload}
                isDownloading={isDownloading}
              />
            ) : (
              <iframe
                src={pdfObjectUrl}
                title={filename}
                className="w-full h-full rounded-xl border border-borderColor bg-white shadow-inner"
              />
            )
          ) : isCodeOrText ? (
            <div className="w-full h-full bg-bgSecondary border border-borderColor rounded-xl overflow-hidden flex flex-col">
              <div className="p-2.5 bg-bgHeader border-b border-borderColor text-[11px] font-mono text-textMuted flex items-center justify-between">
                <span>{filename}</span>
                <span>UTF-8</span>
              </div>
              <div className="flex-1 p-4 font-mono text-xs text-textPrimary overflow-auto whitespace-pre-wrap select-text leading-relaxed">
                {isLoadingText ? (
                  <div className="flex items-center justify-center h-full text-textMuted">
                    <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading text content...
                  </div>
                ) : textError ? (
                  <div className="flex flex-col items-center justify-center h-full space-y-3 p-4">
                    <p className="text-dangerText font-medium text-xs">{textError}</p>
                    <button
                      type="button"
                      onClick={loadTextContent}
                      className="px-3 py-1.5 bg-accent text-white rounded-lg text-xs font-semibold hover:bg-accent/90 transition-colors flex items-center space-x-1.5"
                    >
                      <RotateCw className="w-3.5 h-3.5" />
                      <span>Retry</span>
                    </button>
                  </div>
                ) : (
                  textContent
                )}
              </div>
            </div>
          ) : (
            <GenericFilePreview
              item={item}
              categoryLabel={caps.categoryLabel}
              onDownload={handleDownload}
              isDownloading={isDownloading}
            />
          )}
        </div>
      </div>
    </div>
  );
}
