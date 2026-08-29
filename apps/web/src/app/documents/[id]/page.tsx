'use client';

import React, { useState } from 'react';
import { useParams } from 'next/navigation';
import { useAuthStore } from '../../../features/auth/auth-store';
import { useDocumentDetails } from '../../../features/documents/hooks';
import * as api from '../../../features/documents/api';
import DocumentPreview from '../../../features/documents/components/DocumentPreview';
import MetadataPanel from '../../../features/documents/components/MetadataPanel';
import VersionHistory from '../../../features/documents/components/VersionHistory';
import ProcessingStatus from '../../../features/documents/components/ProcessingStatus';

export default function DocumentDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const { token, currentOrg } = useAuthStore();
  const orgId = currentOrg?.id || '';
  const [activeTab, setActiveTab] = useState<'metadata' | 'versions' | 'processing'>('metadata');

  const { document: doc, loading, refetch } = useDocumentDetails(token, orgId, id);

  const handleReprocess = async () => {
    if (!doc) return;
    try {
      await api.reprocessDocument(token, orgId, doc.id);
      alert("Manually triggered scanned PDF OCR reprocessing pipeline job.");
      refetch();
    } catch (err) {
      alert("Reprocess trigger failed: " + err);
    }
  };

  if (loading || !doc) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bgPrimary text-textPrimary font-outfit">
        <span className="animate-pulse text-textMuted">Loading Document Preview details...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bgPrimary text-textPrimary p-8 space-y-6 font-outfit">
      <div className="flex justify-between items-center bg-bgCard border border-borderColor p-5 rounded-2xl backdrop-blur-xl">
        <div className="flex items-center gap-4">
          <a
            href="/documents"
            className="p-2 rounded-xl bg-bgTertiary hover:bg-bgHover text-textMuted hover:text-textPrimary transition border border-borderMuted"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
            </svg>
          </a>
          <div>
            <h1 className="text-xl font-bold truncate max-w-xs sm:max-w-md text-textPrimary">{doc.title || doc.filename}</h1>
            <p className="text-xs text-textMuted">Uploaded on {new Date(doc.created_at).toLocaleString()}</p>
          </div>
        </div>

        <button
          onClick={handleReprocess}
          className="px-4 py-2 rounded-xl bg-accent hover:bg-accentHover text-xs font-semibold text-white transition active:scale-95 shadow-md shadow-accent/35"
        >
          Reprocess OCR
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        <div className="lg:col-span-2 space-y-6">
          <DocumentPreview doc={doc} token={token} orgId={orgId} />
        </div>

        <div className="space-y-6">
          <div className="flex bg-bgTertiary border border-borderMuted p-1 rounded-xl">
            <button
              onClick={() => setActiveTab('metadata')}
              className={`flex-1 py-2 text-center rounded-lg text-xs font-semibold transition ${
                activeTab === 'metadata' ? 'bg-accent text-white' : 'text-textMuted hover:text-textPrimary'
              }`}
            >
              Metadata
            </button>
            <button
              onClick={() => setActiveTab('versions')}
              className={`flex-1 py-2 text-center rounded-lg text-xs font-semibold transition ${
                activeTab === 'versions' ? 'bg-accent text-white' : 'text-textMuted hover:text-textPrimary'
              }`}
            >
              Versions
            </button>
            <button
              onClick={() => setActiveTab('processing')}
              className={`flex-1 py-2 text-center rounded-lg text-xs font-semibold transition ${
                activeTab === 'processing' ? 'bg-accent text-white' : 'text-textMuted hover:text-textPrimary'
              }`}
            >
              Status
            </button>
          </div>

          {activeTab === 'metadata' && (
            <MetadataPanel doc={doc} token={token} orgId={orgId} onUpdateSuccess={refetch} />
          )}

          {activeTab === 'versions' && (
            <VersionHistory doc={doc} token={token} orgId={orgId} onRestoreSuccess={refetch} />
          )}

          {activeTab === 'processing' && (
            <ProcessingStatus doc={doc} token={token} orgId={orgId} />
          )}
        </div>
      </div>
    </div>
  );
}
