'use client';

import React, { useEffect, useState, useRef } from 'react';
import { useAuthStore } from '../../features/auth/auth-store';
import { useWorkspaceStore } from '../../features/workspace/store';
import { useDocumentsStore } from '../../features/documents/store';
import { useDocumentsList } from '../../features/documents/hooks';
import * as api from '../../features/documents/api';
import { validateDocumentFile, formatHumanReadableError } from '../../features/documents/utils';
import { Document } from '../../features/documents/types';
import DocumentLibrary from '../../features/documents/components/DocumentLibrary';
import UploadCenter from '../../features/documents/components/UploadCenter';
import UploadQueue from '../../features/documents/components/UploadQueue';
import UploadProgress from '../../features/documents/components/UploadProgress';
import BulkToolbar from '../../features/documents/components/BulkToolbar';
import DeleteDialog from '../../features/documents/components/DeleteDialog';
import RenameDialog from '../../features/documents/components/RenameDialog';
import { FilePreviewModal } from '../../features/files/components/FilePreviewModal';
import { FileText, Clock, Star, Trash2, AlertCircle } from 'lucide-react';

export default function DocumentsPage() {
  const { token, currentOrg } = useAuthStore();
  const { currentWorkspace, fetchWorkspaces } = useWorkspaceStore();

  const orgId = currentOrg?.id || '';
  const workspaceId = currentWorkspace?.id || '';

  useEffect(() => {
    if (token && orgId && !currentWorkspace) {
      fetchWorkspaces(token, orgId);
    }
  }, [token, orgId, currentWorkspace, fetchWorkspaces]);

  const {
    viewCategory,
    setViewCategory,
    selectedDocumentIds,
    toggleSelectDocumentId,
    setSelectedDocumentIds,
    uploadQueue,
    addUploadQueueItem,
    updateUploadProgress
  } = useDocumentsStore();

  const { documents, loading, error: fetchError, refetch } = useDocumentsList(
    token,
    orgId,
    workspaceId,
    undefined,
    undefined,
    viewCategory
  );

  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [docToDelete, setDocToDelete] = useState<Document | null>(null);

  const [isRenameOpen, setIsRenameOpen] = useState(false);
  const [docToRename, setDocToRename] = useState<Document | null>(null);

  const [pageError, setPageError] = useState<string | null>(null);

  // Map to hold AbortControllers for actively uploading items
  const abortControllersRef = useRef<{ [id: string]: AbortController }>({});
  // Map to store files for retry
  const fileMapRef = useRef<{ [id: string]: File }>({});

  const handleFilesSelected = async (files: FileList) => {
    setPageError(null);
    const existingNames = documents.map((d) => d.filename);

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const uploadId = Math.random().toString(36).substring(7);

      // Validate File
      const val = validateDocumentFile(file, existingNames);
      if (!val.valid) {
        addUploadQueueItem({
          id: uploadId,
          name: file.name,
          size: file.size,
          progress: 0,
          status: 'failed',
          error: val.error,
          file,
        });
        continue;
      }

      fileMapRef.current[uploadId] = file;
      await startSingleFileUpload(uploadId, file);
    }
    refetch();
  };

  const startSingleFileUpload = async (uploadId: string, file: File) => {
    const controller = new AbortController();
    abortControllersRef.current[uploadId] = controller;

    addUploadQueueItem({
      id: uploadId,
      name: file.name,
      size: file.size,
      progress: 5,
      status: 'uploading',
      file,
    });

    try {
      const uploadedDoc = await api.uploadDocument(
        token,
        orgId,
        workspaceId,
        undefined,
        file,
        undefined,
        file.name,
        'private',
        (percent) => {
          updateUploadProgress(uploadId, percent, 'uploading');
        },
        controller.signal
      );

      // Reset stale error state and refresh document list immediately
      setPageError(null);
      updateUploadProgress(uploadId, 100, 'completed');
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('mindmesh:document-changed'));
      await refetch();
    } catch (err: any) {
      if (err.message === 'Upload cancelled.') {
        updateUploadProgress(uploadId, 0, 'cancelled', undefined, undefined, 'Upload cancelled by user.');
      } else {
        const readableErr = formatHumanReadableError(err);
        updateUploadProgress(uploadId, 0, 'failed', undefined, undefined, readableErr);
      }
    } finally {
      delete abortControllersRef.current[uploadId];
    }
  };

  const handleCancelUpload = (uploadId: string) => {
    if (abortControllersRef.current[uploadId]) {
      abortControllersRef.current[uploadId].abort();
      delete abortControllersRef.current[uploadId];
    }
    updateUploadProgress(uploadId, 0, 'cancelled', undefined, undefined, 'Upload cancelled.');
  };

  const handleRetryUpload = (uploadId: string) => {
    const file = fileMapRef.current[uploadId];
    if (file) {
      startSingleFileUpload(uploadId, file);
    }
  };

  const handleRenameConfirm = async (newTitle: string) => {
    if (!docToRename) return;
    try {
      await api.updateDocument(token, orgId, docToRename.id, { title: newTitle });
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('mindmesh:document-changed'));
      refetch();
    } catch (err: any) {
      throw new Error(formatHumanReadableError(err));
    }
  };

  const handleDeleteSingle = async (doc: Document) => {
    setDocToDelete(doc);
    setIsDeleteOpen(true);
  };

  const handleConfirmDelete = async () => {
    try {
      const isPermanent = viewCategory === 'trash';
      if (docToDelete) {
        await api.deleteDocument(token, orgId, docToDelete.id, isPermanent);
        setDocToDelete(null);
      } else {
        for (const id of selectedDocumentIds) {
          await api.deleteDocument(token, orgId, id, isPermanent);
        }
        setSelectedDocumentIds([]);
      }
      setIsDeleteOpen(false);
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('mindmesh:document-changed'));
      await refetch();
    } catch (err: any) {
      setPageError(formatHumanReadableError(err));
    }
  };

  const handleRestore = async (doc: Document) => {
    try {
      await api.restoreDocument(token, orgId, doc.id);
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('mindmesh:data-changed'));
      refetch();
    } catch (err: any) {
      setPageError(formatHumanReadableError(err));
    }
  };

  const handleDownload = async (doc: Document) => {
    try {
      await api.downloadDocumentFile(token, orgId, doc.id, doc.filename || doc.title || 'document');
    } catch (err: any) {
      setPageError(formatHumanReadableError(err));
    }
  };

  const [previewDoc, setPreviewDoc] = useState<Document | null>(null);

  const onSelectDoc = (id: string) => {
    const doc = documents.find((d) => d.id === id);
    if (doc) setPreviewDoc(doc);
  };

  const previewItem = previewDoc
    ? {
        id: previewDoc.id,
        organization_id: previewDoc.organization_id || orgId,
        uploaded_by: previewDoc.uploaded_by || '',
        uploader_name: 'Workspace Member',
        original_filename: previewDoc.filename || previewDoc.title || 'document',
        storage_filename: previewDoc.stored_filename || previewDoc.filename || '',
        mime_type: previewDoc.mime_type || (previewDoc.extension === 'pdf' ? 'application/pdf' : 'application/octet-stream'),
        file_size: previewDoc.size || previewDoc.file_size || 0,
        storage_path: previewDoc.storage_path || '',
        preview_url: `/api/v1/documents/${previewDoc.id}/download`,
        download_url: `/api/v1/documents/${previewDoc.id}/download`,
        version: previewDoc.version || 1,
        status: 'active',
        created_at: previewDoc.created_at || new Date().toISOString(),
        updated_at: previewDoc.updated_at || new Date().toISOString(),
      }
    : null;

  return (
    <div className="space-y-4 font-outfit text-textPrimary">
      {/* Header & Tabs */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-bgCard border border-borderColor p-4 rounded-2xl backdrop-blur-xl">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-textPrimary">
            Knowledge Workspace
          </h1>
          <p className="text-xs text-textMuted mt-0.5">
            Organize, search, preview, and build knowledge intelligence from workspace documents.
          </p>
        </div>

        {/* View Category Tabs */}
        <div className="flex bg-bgTertiary border border-borderMuted p-1 rounded-xl text-xs font-semibold">
          <button
            onClick={() => setViewCategory('all')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
              viewCategory === 'all' ? 'bg-accent text-white shadow-sm' : 'text-textMuted hover:text-textPrimary'
            }`}
          >
            <FileText size={13} /> All
          </button>
          <button
            onClick={() => setViewCategory('recent')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
              viewCategory === 'recent' ? 'bg-accent text-white shadow-sm' : 'text-textMuted hover:text-textPrimary'
            }`}
          >
            <Clock size={13} /> Recent
          </button>
          <button
            onClick={() => setViewCategory('favorites')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
              viewCategory === 'favorites' ? 'bg-accent text-white shadow-sm' : 'text-textMuted hover:text-textPrimary'
            }`}
          >
            <Star size={13} /> Favorites
          </button>
          <button
            onClick={() => setViewCategory('trash')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition ${
              viewCategory === 'trash' ? 'bg-accent text-white shadow-sm' : 'text-textMuted hover:text-textPrimary'
            }`}
          >
            <Trash2 size={13} /> Trash
          </button>
        </div>
      </div>

      {/* Page Level Error Banner */}
      {(pageError || fetchError) && (
        <div className="flex items-center justify-between bg-dangerBg border border-dangerBorder p-3 rounded-xl text-xs text-dangerText">
          <div className="flex items-center gap-2">
            <AlertCircle size={15} />
            <span>{pageError || fetchError}</span>
          </div>
          <button
            onClick={() => setPageError(null)}
            className="text-dangerText hover:underline text-[11px] font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-start">
        <div className="lg:col-span-2 space-y-4">
          <DocumentLibrary
            documents={documents}
            selectedIds={selectedDocumentIds}
            loading={loading}
            onToggleSelect={toggleSelectDocumentId}
            onSelectDoc={onSelectDoc}
            onUploadTrigger={() => document.getElementById('browse-trigger')?.click()}
            onRename={(doc) => { setDocToRename(doc); setIsRenameOpen(true); }}
            onDelete={handleDeleteSingle}
            onRestore={handleRestore}
            onDownload={handleDownload}
            isTrashView={viewCategory === 'trash'}
          />
        </div>

        <div className="space-y-4">
          <UploadCenter onFilesSelected={handleFilesSelected} />
          <UploadQueue
            onCancel={handleCancelUpload}
            onRetry={handleRetryUpload}
          />
        </div>
      </div>

      <UploadProgress />

      <BulkToolbar
        selectedCount={selectedDocumentIds.length}
        onClear={() => setSelectedDocumentIds([])}
        onDelete={() => { setDocToDelete(null); setIsDeleteOpen(true); }}
      />

      <DeleteDialog
        isOpen={isDeleteOpen}
        onClose={() => { setIsDeleteOpen(false); setDocToDelete(null); }}
        onConfirm={handleConfirmDelete}
        count={docToDelete ? 1 : selectedDocumentIds.length}
      />

      <RenameDialog
        isOpen={isRenameOpen}
        onClose={() => { setIsRenameOpen(false); setDocToRename(null); }}
        onConfirm={handleRenameConfirm}
        document={docToRename}
      />

      {/* Universal Shared Preview Modal */}
      <FilePreviewModal item={previewItem} onClose={() => setPreviewDoc(null)} />
    </div>
  );
}
