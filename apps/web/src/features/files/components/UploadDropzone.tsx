import React, { useState, useRef } from 'react';
import { UploadCloud, File, X, Loader2, CheckCircle } from 'lucide-react';
import { uploadFile, AttachmentItem } from '../files-api';

interface UploadDropzoneProps {
  conversationId: string;
  messageId?: string;
  onUploadSuccess: (attachment: AttachmentItem) => void;
  token?: string;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({
  conversationId,
  messageId,
  onUploadSuccess,
  token
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const processFile = async (file: File) => {
    setIsUploading(true);
    setProgress(0);
    setError(null);
    try {
      const att = await uploadFile(file, conversationId, messageId, (p) => setProgress(p), token);
      onUploadSuccess(att);
    } catch (err: any) {
      setError(err.message || 'File upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      await processFile(file);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await processFile(e.target.files[0]);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-2xl p-4 text-center transition-all ${
        isDragging
          ? 'border-accent bg-accentSubtle'
          : 'border-borderColor hover:border-borderHover bg-bgCard'
      }`}
    >
      <input
        id="upload-file-attachment"
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        aria-label="Upload file attachment"
        className="hidden"
      />

      {isUploading ? (
        <div className="space-y-2 py-2" role="status" aria-live="polite">
          <div className="flex items-center justify-center space-x-2 text-accentText text-xs font-semibold">
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
            <span>Uploading Attachment ({progress}%)</span>
          </div>
          <div 
            role="progressbar" 
            aria-valuenow={progress} 
            aria-valuemin={0} 
            aria-valuemax={100} 
            aria-label={`Uploading attachment progress ${progress}%`}
            className="w-full bg-bgTertiary rounded-full h-1.5 overflow-hidden max-w-xs mx-auto"
          >
            <div className="bg-accent h-full transition-all duration-200" style={{ width: `${progress}%` }} />
          </div>
        </div>
      ) : (
        <div 
          role="button"
          tabIndex={0}
          aria-label="Drag and drop files here or browse to upload"
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          className="flex items-center justify-between cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded-xl p-1" 
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-accentSubtle text-accentText border border-accent/30" aria-hidden="true">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div className="text-left">
              <p className="text-xs font-medium text-textPrimary">Drag & drop files here or <span className="text-accentText underline">browse</span></p>
              <p className="text-[10px] text-textMuted">Supports Images, Documents, Code, Archives (Max 50 MB)</p>
            </div>
          </div>
        </div>
      )}

      {error && (
        <p role="alert" className="text-dangerText text-[11px] mt-2 bg-dangerBg border border-dangerBorder p-2 rounded-lg">
          {error}
        </p>
      )}
    </div>
  );
};
