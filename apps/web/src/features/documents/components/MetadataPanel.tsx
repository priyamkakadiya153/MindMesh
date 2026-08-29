import React, { useState, useEffect } from 'react';
import { Document, DocumentMetadata } from '../types';
import * as api from '../api';

interface MetadataPanelProps {
  doc: Document;
  token: string;
  orgId: string;
  onUpdateSuccess?: () => void;
}

export const MetadataPanel: React.FC<MetadataPanelProps> = ({
  doc,
  token,
  orgId,
  onUpdateSuccess
}) => {
  const [meta, setMeta] = useState<DocumentMetadata | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [author, setAuthor] = useState('');
  const [confidentiality, setConfidentiality] = useState('internal');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await api.getDocumentMetadata(token, orgId, doc.id);
        setMeta(data);
        setTitle(data.title || doc.filename);
        setDescription(data.description || '');
        setAuthor(data.author || '');
        setConfidentiality(data.confidentiality || 'internal');
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [doc.id, token, orgId]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      const updated = await api.updateDocumentMetadata(token, orgId, doc.id, {
        title,
        description,
        author,
        confidentiality
      });
      setMeta(updated);
      if (onUpdateSuccess) onUpdateSuccess();
    } catch (err) {
      alert("Failed to save metadata: " + err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-white/40 text-xs animate-pulse p-4">Loading metadata fields...</div>;
  }

  return (
    <form onSubmit={handleSave} className="space-y-4 p-5 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl">
      <h3 className="text-sm font-bold text-white mb-2 font-outfit">Document Metadata</h3>

      <div>
        <label className="block text-[11px] font-semibold text-white/50 uppercase mb-1">Title</label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 transition"
          required
        />
      </div>

      <div>
        <label className="block text-[11px] font-semibold text-white/50 uppercase mb-1">Author</label>
        <input
          type="text"
          value={author}
          onChange={(e) => setAuthor(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 transition"
        />
      </div>

      <div>
        <label className="block text-[11px] font-semibold text-white/50 uppercase mb-1">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 transition resize-none"
        />
      </div>

      <div>
        <label className="block text-[11px] font-semibold text-white/50 uppercase mb-1">Confidentiality</label>
        <select
          value={confidentiality}
          onChange={(e) => setConfidentiality(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 transition"
        >
          <option value="public" className="bg-neutral-900">Public</option>
          <option value="internal" className="bg-neutral-900">Internal</option>
          <option value="confidential" className="bg-neutral-900">Confidential</option>
          <option value="restricted" className="bg-neutral-900">Restricted</option>
        </select>
      </div>

      <div className="pt-2">
        <button
          type="submit"
          disabled={saving}
          className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition active:scale-95 shadow-md shadow-indigo-600/30"
        >
          {saving ? 'Saving...' : 'Save Metadata'}
        </button>
      </div>
    </form>
  );
};
export default MetadataPanel;
