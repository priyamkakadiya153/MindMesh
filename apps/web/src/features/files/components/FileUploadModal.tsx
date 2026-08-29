import React, { useState, useRef } from 'react';
import { X, UploadCloud, File, AlertCircle, RefreshCw, CheckCircle2, ShieldCheck, Loader2 } from 'lucide-react';
import { uploadFile, uploadFileVersion, AttachmentItem, DuplicateFileErrorPayload } from '../files-api';
import { DuplicateDialog } from './DuplicateDialog';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (item: AttachmentItem) => void;
  organizationId?: string;
  workspaceId?: string;
  folderId?: string;
  token?: string;
}

interface UploadTask {
  id: string;
  file: File;
  progress: number;
  status: 'queued' | 'uploading' | 'processing' | 'scanning' | 'completed' | 'error' | 'cancelled';
  errorMessage?: string;
  abortFn?: () => void;
  duplicateInfo?: DuplicateFileErrorPayload;
}

const MAX_SIZE_MB = 50;

export function FileUploadModal({
  isOpen,
  onClose,
  onUploadSuccess,
  organizationId,
  workspaceId,
  folderId,
  token
}: FileUploadModalProps) {
  const [tasks, setTasks] = useState<UploadTask[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [activeDuplicateTask, setActiveDuplicateTask] = useState<UploadTask | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const processFileSelection = (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const newTasks: UploadTask[] = fileArray.map((file) => ({
      id: Math.random().toString(36).substring(2, 9),
      file,
      progress: 0,
      status: 'queued'
    }));

    setTasks((prev) => [...prev, ...newTasks]);

    newTasks.forEach((task) => {
      startTaskUpload(task, false);
    });
  };

  const startTaskUpload = async (task: UploadTask, forceDuplicate: boolean = false) => {
    if (task.file.size > MAX_SIZE_MB * 1024 * 1024) {
      setTasks((prev) =>
        prev.map((t) =>
          t.id === task.id
            ? { ...t, status: 'error', errorMessage: `Maximum size exceeded (50 MB limit).` }
            : t
        )
      );
      return;
    }

    setTasks((prev) =>
      prev.map((t) => (t.id === task.id ? { ...t, status: 'uploading', progress: 0 } : t))
    );

    try {
      const uploadedItem = await uploadFile({
        file: task.file,
        organizationId,
        workspaceId,
        folderId,
        token,
        forceDuplicate,
        onProgress: (percent) => {
          setTasks((prev) =>
            prev.map((t) => (t.id === task.id ? { ...t, progress: percent } : t))
          );
        },
        onAbortRef: (abortFn) => {
          setTasks((prev) =>
            prev.map((t) => (t.id === task.id ? { ...t, abortFn } : t))
          );
        }
      });

      setTasks((prev) =>
        prev.map((t) =>
          t.id === task.id ? { ...t, status: 'completed', progress: 100 } : t
        )
      );

      onUploadSuccess(uploadedItem);
    } catch (err: any) {
      if (err.isDuplicate && err.duplicateInfo) {
        setTasks((prev) =>
          prev.map((t) =>
            t.id === task.id ? { ...t, duplicateInfo: err.duplicateInfo } : t
          )
        );
        setActiveDuplicateTask(task);
      } else if (err.message === 'Upload cancelled') {
        setTasks((prev) =>
          prev.map((t) => (t.id === task.id ? { ...t, status: 'cancelled', progress: 0 } : t))
        );
      } else {
        setTasks((prev) =>
          prev.map((t) =>
            t.id === task.id
              ? {
                  ...t,
                  status: 'error',
                  errorMessage: err.message || 'Upload failed due to a network error'
                }
              : t
          )
        );
      }
    }
  };

  const handleReplaceVersion = async () => {
    if (!activeDuplicateTask || !activeDuplicateTask.duplicateInfo) return;
    const task = activeDuplicateTask;
    const dupInfo = task.duplicateInfo;
    setActiveDuplicateTask(null);

    try {
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, status: 'uploading', progress: 50 } : t))
      );
      const updated = await uploadFileVersion(dupInfo.existing_file_id, task.file, token);
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, status: 'completed', progress: 100 } : t))
      );
      onUploadSuccess(updated);
    } catch (err: any) {
      setTasks((prev) =>
        prev.map((t) =>
          t.id === task.id
            ? { ...t, status: 'error', errorMessage: err.message || 'Failed to replace version' }
            : t
        )
      );
    }
  };

  const handleUploadCopy = () => {
    if (!activeDuplicateTask) return;
    const task = activeDuplicateTask;
    setActiveDuplicateTask(null);
    startTaskUpload(task, true);
  };

  const handleCancelDuplicate = () => {
    if (!activeDuplicateTask) return;
    const task = activeDuplicateTask;
    setActiveDuplicateTask(null);
    setTasks((prev) =>
      prev.map((t) => (t.id === task.id ? { ...t, status: 'cancelled', progress: 0 } : t))
    );
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFileSelection(e.dataTransfer.files);
    }
  };

  const handleCancelTask = (task: UploadTask) => {
    if (task.abortFn) {
      task.abortFn();
    } else {
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, status: 'cancelled' } : t))
      );
    }
  };

  const handleRetryTask = (task: UploadTask) => {
    startTaskUpload(task, false);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-bgCard border border-borderColor rounded-2xl w-full max-w-xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-4 border-b border-borderColor flex items-center justify-between bg-bgSecondary">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-accentSubtle text-accentText">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-textPrimary">Upload Files</h3>
              <p className="text-[11px] text-textMuted mt-0.5">
                Add documents, code, images, or archives to shared workspace knowledge
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

        {/* Dropzone */}
        <div className="p-4 overflow-y-auto space-y-4">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
              isDragging
                ? 'border-accent bg-accentSubtle/30 scale-[0.99]'
                : 'border-borderColor hover:border-borderHover bg-bgTertiary/50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  processFileSelection(e.target.files);
                }
              }}
            />
            <UploadCloud className="w-10 h-10 text-accentText mx-auto mb-2 opacity-80" />
            <p className="text-xs font-semibold text-textPrimary">
              Drag and drop files here, or <span className="text-accentText underline">browse</span>
            </p>
            <p className="text-[11px] text-textMuted mt-1">
              PDF, DOCX, PPTX, XLSX, Images, ZIP, CSV, JSON, Code files (Up to 50 MB)
            </p>
          </div>

          {/* Queue List */}
          {tasks.length > 0 && (
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              <div className="flex items-center justify-between text-[11px] font-semibold text-textMuted px-1">
                <span>Upload Queue ({tasks.length})</span>
                <button
                  onClick={() => setTasks([])}
                  className="text-textMuted hover:text-textPrimary transition-colors"
                >
                  Clear Queue
                </button>
              </div>

              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="p-3 bg-bgTertiary border border-borderColor rounded-xl flex items-center justify-between text-xs space-x-3"
                >
                  <div className="flex items-center space-x-3 min-w-0 flex-1">
                    <div className="p-2 rounded-lg bg-bgCard shrink-0">
                      <File className="w-4 h-4 text-accentText" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-textPrimary truncate max-w-[200px]">
                          {task.file.name}
                        </span>
                        <span className="text-[10px] text-textMuted ml-2">
                          {formatSize(task.file.size)}
                        </span>
                      </div>

                      {/* Status states */}
                      {task.status === 'uploading' && (
                        <div className="w-full bg-bgInput rounded-full h-1.5 mt-2 overflow-hidden">
                          <div
                            className="bg-accent h-full transition-all duration-200"
                            style={{ width: `${task.progress}%` }}
                          />
                        </div>
                      )}

                      {task.status === 'error' && (
                        <p className="text-[10px] text-dangerText mt-1 flex items-center">
                          <AlertCircle className="w-3 h-3 mr-1 shrink-0" />
                          {task.errorMessage}
                        </p>
                      )}

                      {task.status === 'completed' && (
                        <p className="text-[10px] text-emerald-400 mt-1 flex items-center">
                          <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-400" />
                          <ShieldCheck className="w-3 h-3 mr-1 text-blue-400" />
                          Safe & Indexed
                        </p>
                      )}

                      {task.status === 'cancelled' && (
                        <p className="text-[10px] text-textMuted mt-1">Upload cancelled</p>
                      )}
                    </div>
                  </div>

                  <div className="shrink-0 flex items-center space-x-1">
                    {task.status === 'uploading' && (
                      <button
                        onClick={() => handleCancelTask(task)}
                        className="p-1 hover:bg-bgHover text-textMuted hover:text-dangerText rounded-lg"
                        title="Cancel Upload"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}

                    {(task.status === 'error' || task.status === 'cancelled') && (
                      <button
                        onClick={() => handleRetryTask(task)}
                        className="p-1 hover:bg-bgHover text-textMuted hover:text-accentText rounded-lg"
                        title="Retry Upload"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3.5 border-t border-borderColor bg-bgSecondary flex items-center justify-between">
          <span className="text-[11px] text-textMuted">
            {tasks.filter((t) => t.status === 'completed').length} of {tasks.length} uploaded
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-accent hover:bg-accentHover text-white text-xs font-semibold transition-colors"
          >
            Done
          </button>
        </div>
      </div>

      {/* Duplicate Resolution Modal */}
      <DuplicateDialog
        isOpen={!!activeDuplicateTask}
        duplicateInfo={activeDuplicateTask?.duplicateInfo || null}
        onCancel={handleCancelDuplicate}
        onReplaceVersion={handleReplaceVersion}
        onUploadCopy={handleUploadCopy}
      />
    </div>
  );
}
