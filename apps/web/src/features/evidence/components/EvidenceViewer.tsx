import React from 'react';
import { useNavigate } from 'react-router-dom';
import { EvidenceItem, ConflictItem } from '../evidence-api';
import { ShieldCheck, AlertTriangle, FileText, ExternalLink, Clock, AlertCircle, Trash2, CheckCircle2 } from 'lucide-react';

interface EvidenceViewerProps {
  trustRating?: string;
  verifiedItems: EvidenceItem[];
  conflicts?: ConflictItem[];
  onOpenSource?: (deepLink: string) => void;
}

export const EvidenceViewer: React.FC<EvidenceViewerProps> = ({
  trustRating = 'STRONG_EVIDENCE',
  verifiedItems,
  conflicts = [],
  onOpenSource
}) => {
  const navigate = useNavigate();

  const getTrustBadge = (rating: string) => {
    switch (rating.toUpperCase()) {
      case 'STRONG_EVIDENCE':
        return (
          <span className="px-2.5 py-0.5 rounded-lg text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center space-x-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>STRONG EVIDENCE</span>
          </span>
        );
      case 'CONFLICTING_EVIDENCE':
        return (
          <span className="px-2.5 py-0.5 rounded-lg text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center space-x-1">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>CONFLICT DETECTED</span>
          </span>
        );
      case 'SOURCE_UNAVAILABLE':
        return (
          <span className="px-2.5 py-0.5 rounded-lg text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center space-x-1">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>SOURCE UNAVAILABLE</span>
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-lg text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center space-x-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>VERIFIED CITATIONS</span>
          </span>
        );
    }
  };

  const handleSourceClick = (link?: string) => {
    if (!link) return;
    if (onOpenSource) {
      onOpenSource(link);
    } else {
      navigate(link);
    }
  };

  if (verifiedItems.length === 0 && conflicts.length === 0) {
    return null;
  }

  return (
    <div className="w-full bg-slate-950/80 border border-slate-800 p-4 rounded-2xl space-y-3 font-sans">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-bold text-slate-200">Grounded Source Evidence</span>
        </div>
        {getTrustBadge(trustRating)}
      </div>

      {/* Conflict Warning Box (if any) */}
      {conflicts.length > 0 && (
        <div className="bg-rose-950/30 border border-rose-500/30 p-3 rounded-xl space-y-1.5 text-xs">
          {conflicts.map((c) => (
            <div key={c.id} className="space-y-1">
              <div className="flex items-center space-x-1.5 text-rose-400 font-bold">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{c.title}</span>
              </div>
              <p className="text-[11px] text-slate-300 pl-5">{c.summary}</p>
            </div>
          ))}
        </div>
      )}

      {/* Verified Citations List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
        {verifiedItems.map((item) => (
          <div
            key={item.id}
            className={`p-3 rounded-xl border transition-all text-xs space-y-1.5 ${
              item.status === 'DELETED'
                ? 'bg-slate-950/40 border-slate-800/60 opacity-75'
                : 'bg-slate-900/60 hover:bg-slate-900 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center space-x-1.5 font-semibold text-slate-100">
                <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 bg-indigo-950 text-indigo-300 rounded border border-indigo-800/60">
                  {item.source_type}
                </span>
                <span className="truncate max-w-[160px]">{item.title}</span>
              </div>

              {item.status === 'DELETED' ? (
                <span className="text-[9px] font-mono text-rose-400 flex items-center space-x-1">
                  <Trash2 className="w-3 h-3" />
                  <span>DELETED</span>
                </span>
              ) : item.status === 'SUPERSEDED' ? (
                <span className="text-[9px] font-mono text-amber-400 flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>SUPERSEDED</span>
                </span>
              ) : (
                <span className="text-[9px] font-mono text-emerald-400 flex items-center space-x-1">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>AVAILABLE</span>
                </span>
              )}
            </div>

            <p className="text-[11px] text-slate-300 italic line-clamp-2 leading-relaxed bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
              "{item.excerpt}"
            </p>

            <div className="flex items-center justify-between text-[10px] text-slate-500 pt-0.5">
              <span>{item.location || 'Verified Document'}</span>

              {item.deep_link && item.status !== 'DELETED' && (
                <button
                  type="button"
                  onClick={() => handleSourceClick(item.deep_link)}
                  className="text-indigo-400 hover:text-indigo-300 font-semibold flex items-center space-x-1"
                >
                  <span>Open Source</span>
                  <ExternalLink className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};
