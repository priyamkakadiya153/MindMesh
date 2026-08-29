import React, { useEffect, useState } from 'react';
import { Sparkles, Brain, CheckCircle2, FileText, Tag, RefreshCw, AlertCircle } from 'lucide-react';

interface FileIntelligenceData {
  id: string;
  document_id: string;
  summary: string | null;
  topics: string[];
  keywords: string[];
  entities: Array<{ name: string; type: string }>;
  facts: Array<{ fact: string; page?: number; section?: string }>;
  decisions: Array<{ decision: string; page?: number; section?: string }>;
  tasks: Array<{ task: string; deadline?: string; page?: number }>;
  language: string;
  document_type: string;
  status: string;
  error_message?: string;
}

interface FileIntelligenceCardProps {
  documentId: string;
  onAskMindMesh?: (query?: string) => void;
}

export function FileIntelligenceCard({ documentId, onAskMindMesh }: FileIntelligenceCardProps) {
  const [intel, setIntel] = useState<FileIntelligenceData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reprocessing, setReprocessing] = useState<boolean>(false);

  const fetchIntelligence = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token') || '';
      const headers: HeadersInit = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`/api/v1/documents/${documentId}/intelligence`, { headers });
      if (!res.ok) throw new Error('Failed to fetch file intelligence');
      const data = await res.json();
      setIntel(data);
    } catch (err: any) {
      console.error('File intelligence error:', err);
      setError('Unable to load file intelligence.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (documentId) {
      fetchIntelligence();
    }
  }, [documentId]);

  const handleReprocess = async () => {
    setReprocessing(true);
    try {
      const token = localStorage.getItem('token') || '';
      const headers: HeadersInit = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`/api/v1/documents/${documentId}/intelligence/reprocess`, {
        method: 'POST',
        headers
      });
      if (!res.ok) throw new Error('Reprocess failed');
      await fetchIntelligence();
    } catch (err) {
      console.error('Reprocess error:', err);
    } finally {
      setReprocessing(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 animate-pulse space-y-3">
        <div className="flex items-center space-x-2">
          <div className="w-5 h-5 rounded-full bg-slate-800" />
          <div className="h-4 w-36 bg-slate-800 rounded" />
        </div>
        <div className="h-12 bg-slate-800/60 rounded" />
      </div>
    );
  }

  if (error || !intel) {
    return (
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-textMuted flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>{error || 'No intelligence available for this file.'}</span>
        </div>
        <button
          onClick={fetchIntelligence}
          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-textPrimary font-medium transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-4 space-y-4 text-xs text-textPrimary">
      {/* Intelligence Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <h4 className="font-semibold text-textPrimary flex items-center space-x-2">
              <span>MindMesh Intelligence</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                {intel.document_type}
              </span>
            </h4>
            <p className="text-[10px] text-textMuted capitalize">
              Status: <span className={intel.status === 'COMPLETED' ? 'text-emerald-400' : 'text-amber-400'}>{intel.status.toLowerCase()}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleReprocess}
            disabled={reprocessing}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-textMuted hover:text-textPrimary transition-colors"
            title="Re-analyze document intelligence"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reprocessing ? 'animate-spin' : ''}`} />
          </button>

          {onAskMindMesh && (
            <button
              type="button"
              onClick={() => onAskMindMesh(`What are the key insights in this ${intel.document_type}?`)}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition-all shadow-sm"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Ask MindMesh</span>
            </button>
          )}
        </div>
      </div>

      {/* Summary */}
      {intel.summary && (
        <div className="space-y-1">
          <h5 className="text-[11px] font-semibold text-textMuted uppercase tracking-wider flex items-center space-x-1.5">
            <FileText className="w-3.5 h-3.5 text-indigo-400" />
            <span>Summary</span>
          </h5>
          <p className="text-textSecondary leading-relaxed bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/60">
            {intel.summary}
          </p>
        </div>
      )}

      {/* Topics & Keywords */}
      {intel.topics && intel.topics.length > 0 && (
        <div className="space-y-1.5">
          <h5 className="text-[11px] font-semibold text-textMuted uppercase tracking-wider flex items-center space-x-1.5">
            <Tag className="w-3.5 h-3.5 text-purple-400" />
            <span>Topics & Keywords</span>
          </h5>
          <div className="flex flex-wrap gap-1.5">
            {intel.topics.map((topic, i) => (
              <span key={i} className="px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/20 text-[11px]">
                {topic}
              </span>
            ))}
            {intel.keywords && intel.keywords.slice(0, 5).map((kw, i) => (
              <span key={i} className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 text-[11px]">
                #{kw}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Facts & Decisions */}
      {((intel.facts && intel.facts.length > 0) || (intel.decisions && intel.decisions.length > 0)) && (
        <div className="space-y-2">
          <h5 className="text-[11px] font-semibold text-textMuted uppercase tracking-wider flex items-center space-x-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Key Facts & Decisions</span>
          </h5>
          <ul className="space-y-1.5">
            {intel.decisions?.map((d, i) => (
              <li key={`dec-${i}`} className="p-2 rounded-lg bg-indigo-950/30 border border-indigo-800/40 text-indigo-200 text-xs">
                <span className="font-semibold text-indigo-400">Decision: </span>
                {d.decision}
                {d.page && <span className="text-[10px] text-indigo-400/70 ml-2">(Page {d.page})</span>}
              </li>
            ))}
            {intel.facts?.map((f, i) => (
              <li key={`fact-${i}`} className="p-2 rounded-lg bg-slate-950/40 border border-slate-800/60 text-slate-300 text-xs">
                <span className="font-semibold text-emerald-400">Fact: </span>
                {f.fact}
                {f.page && <span className="text-[10px] text-slate-400 ml-2">(Page {f.page})</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
