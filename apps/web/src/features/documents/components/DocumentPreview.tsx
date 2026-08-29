import React, { useEffect, useState } from 'react';
import { Document } from '../types';
import * as api from '../api';
import { Download, FileText, Code, Image as ImageIcon, File, Loader2, Info } from 'lucide-react';

interface DocumentPreviewProps {
  doc: Document;
  token?: string;
  orgId?: string;
}

export const DocumentPreview: React.FC<DocumentPreviewProps> = ({ doc, token, orgId }) => {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const ext = (doc.extension || doc.filename.split('.').pop() || '').toLowerCase();
  const isImage = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext);
  const isCode = ['java', 'py', 'js', 'ts', 'c', 'cpp', 'html', 'css', 'json', 'xml', 'yaml', 'yml', 'sql', 'md'].includes(ext);
  const isPDF = ext === 'pdf';

  useEffect(() => {
    let mounted = true;
    const loadPreview = async () => {
      setLoading(true);
      setError(null);
      try {
        if (token && orgId) {
          const res = await api.getDocumentPreview(token, orgId, doc.id).catch(() => null);
          if (mounted && res) setPreviewData(res);

          if (isImage || isPDF) {
            const url = await api.getDocumentBlobUrl(token, orgId, doc.id).catch(() => null);
            if (mounted) setBlobUrl(url);
          }
        }
      } catch (e: any) {
        if (mounted) setError(e.message || 'Failed to load preview');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    loadPreview();

    return () => {
      mounted = false;
      if (blobUrl) window.URL.revokeObjectURL(blobUrl);
    };
  }, [doc.id, token, orgId]);

  const handleDownload = async () => {
    if (token && orgId) {
      try {
        await api.downloadDocumentFile(token, orgId, doc.id, doc.filename || doc.title || 'document');
      } catch (err: any) {
        alert(err.message || 'Failed to download document.');
      }
    }
  };

  if (loading) {
    return (
      <div className="w-full h-80 flex flex-col items-center justify-center rounded-2xl border border-borderColor bg-bgCard backdrop-blur-xl p-8 text-center text-textMuted space-y-2">
        <Loader2 className="w-6 h-6 animate-spin text-accentText" />
        <span className="text-xs">Generating secure preview...</span>
      </div>
    );
  }

  if (isImage && blobUrl) {
    return (
      <div className="w-full flex flex-col items-center justify-center p-4 rounded-2xl border border-borderColor bg-bgCard backdrop-blur-xl space-y-4">
        <img
          src={blobUrl}
          alt={doc.filename}
          className="max-h-96 max-w-full rounded-xl object-contain shadow-xl border border-borderColor"
        />
        <button
          onClick={handleDownload}
          className="px-4 py-2 bg-accent hover:bg-accentHover text-xs font-semibold text-white rounded-xl flex items-center gap-2 transition"
        >
          <Download className="w-4 h-4" /> Download Original Image
        </button>
      </div>
    );
  }

  if (isCode || previewData?.preview_type === 'code') {
    return (
      <div className="w-full flex flex-col rounded-2xl border border-borderColor bg-bgInput overflow-hidden font-outfit">
        <div className="flex items-center justify-between px-4 py-2.5 bg-bgHeader border-b border-borderColor text-xs text-textSecondary">
          <div className="flex items-center gap-2">
            <Code className="w-4 h-4 text-accentText" />
            <span className="font-mono font-semibold text-accentText">{doc.filename}</span>
          </div>
          <button
            onClick={handleDownload}
            className="flex items-center gap-1 text-[11px] text-accentText hover:underline font-medium"
          >
            <Download className="w-3 h-3" /> Download
          </button>
        </div>
        <pre className="p-4 text-xs font-mono text-emerald-500 overflow-x-auto max-h-96 leading-relaxed select-text">
          <code>{previewData?.text || previewData?.extracted_text_snippet || "// Code snippet preview\n// No text content available"}</code>
        </pre>
      </div>
    );
  }

  if (isPDF && blobUrl) {
    return (
      <div className="w-full flex flex-col rounded-2xl border border-borderColor bg-bgCard p-4 space-y-3 font-outfit">
        <div className="flex justify-between items-center">
          <span className="text-xs font-semibold text-textPrimary">PDF Document Preview</span>
          <button
            onClick={handleDownload}
            className="px-3 py-1.5 bg-accent hover:bg-accentHover text-xs text-white font-medium rounded-lg flex items-center gap-1.5 transition"
          >
            <Download className="w-3.5 h-3.5" /> Download PDF
          </button>
        </div>
        <iframe
          src={blobUrl}
          title={doc.filename}
          className="w-full h-96 rounded-xl border border-borderColor bg-white"
        />
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col items-center justify-center rounded-2xl border border-borderColor bg-bgCard backdrop-blur-xl p-6 text-center font-outfit space-y-4">
      <div className="h-12 w-12 flex items-center justify-center rounded-2xl bg-accentSubtle text-accentText border border-accent/20">
        <FileText className="w-6 h-6" />
      </div>

      <div>
        <h4 className="text-sm font-bold text-textPrimary mb-1">{doc.title || doc.filename}</h4>
        <p className="text-xs text-textMuted max-w-md">
          {previewData?.extracted_text_snippet || "Browser inline preview is not supported for this file type. You can inspect file details below or download the file."}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 w-full max-w-md bg-bgTertiary p-3 rounded-xl border border-borderMuted text-left text-xs">
        <div>
          <span className="text-[10px] text-textMuted uppercase font-semibold block">File Extension</span>
          <span className="font-mono font-medium text-textPrimary uppercase">{ext || 'N/A'}</span>
        </div>
        <div>
          <span className="text-[10px] text-textMuted uppercase font-semibold block">Size</span>
          <span className="font-medium text-textPrimary">{((doc.size || doc.size_bytes || 0) / 1024).toFixed(1)} KB</span>
        </div>
        <div>
          <span className="text-[10px] text-textMuted uppercase font-semibold block">MIME Type</span>
          <span className="font-mono text-[11px] text-textSecondary truncate block">{doc.mime_type || 'application/octet-stream'}</span>
        </div>
        <div>
          <span className="text-[10px] text-textMuted uppercase font-semibold block">Uploaded By</span>
          <span className="text-[11px] text-textSecondary truncate block">{doc.uploaded_by || 'User'}</span>
        </div>
      </div>

      <button
        onClick={handleDownload}
        className="px-5 py-2.5 rounded-xl bg-accent hover:bg-accentHover text-xs font-semibold text-white transition active:scale-95 shadow-lg shadow-accent/20 flex items-center gap-2"
      >
        <Download className="w-4 h-4" /> Download File ({((doc.size || doc.size_bytes || 0) / 1024).toFixed(1)} KB)
      </button>
    </div>
  );
};
export default DocumentPreview;

