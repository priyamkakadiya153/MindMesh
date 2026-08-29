import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchImportantSignals, dismissSignal, IntelligenceSignalItem } from '../intelligence-api';
import {
  Sparkles, AlertTriangle, AlertCircle, CheckCircle2, Clock, HelpCircle,
  FileText, ArrowRight, X, Loader2, ShieldAlert, Zap
} from 'lucide-react';

interface ImportantForYouWidgetProps {
  workspaceId?: string;
  token?: string;
  onAskMindMesh?: (prompt: string) => void;
}

export const ImportantForYouWidget: React.FC<ImportantForYouWidgetProps> = ({
  workspaceId,
  token,
  onAskMindMesh
}) => {
  const navigate = useNavigate();
  const [signals, setSignals] = useState<IntelligenceSignalItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const loadSignals = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchImportantSignals(workspaceId, token);
      setSignals(data);
    } catch (err) {
      console.error('Failed to load proactive signals:', err);
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, token]);

  useEffect(() => {
    loadSignals();
  }, [loadSignals]);

  const handleDismiss = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await dismissSignal(id, token);
      setSignals((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      console.error('Failed to dismiss signal:', err);
    }
  };

  const handleAskAboutSignal = (sig: IntelligenceSignalItem) => {
    const promptText = `Explain this proactive intelligence signal: "${sig.title}" - ${sig.summary}`;
    if (onAskMindMesh) {
      onAskMindMesh(promptText);
    } else {
      navigate('/ask', { state: { initialPrompt: promptText } });
    }
  };

  const getSignalIcon = (type: string, priority: string) => {
    if (priority === 'HIGH' || type === 'BLOCKED_TASK' || type === 'KNOWLEDGE_CONFLICT') {
      return <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />;
    }
    if (type === 'OVERDUE_TASK') {
      return <Clock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />;
    }
    if (type === 'NEW_DECISION') {
      return <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />;
    }
    if (type === 'OPEN_QUESTION') {
      return <HelpCircle className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />;
    }
    return <Zap className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />;
  };

  if (isLoading) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-3xl space-y-3">
        <div className="flex items-center space-x-2 text-slate-400 text-xs">
          <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
          <span>Scanning proactive workspace intelligence...</span>
        </div>
      </div>
    );
  }

  if (signals.length === 0) {
    return (
      <div className="bg-slate-900/40 border border-slate-800/80 p-5 rounded-3xl text-center space-y-1">
        <Sparkles className="w-5 h-5 text-indigo-400 mx-auto" />
        <h4 className="text-xs font-bold text-slate-300">You're all caught up</h4>
        <p className="text-[11px] text-slate-500">No urgent proactive intelligence signals require attention right now.</p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-indigo-400 animate-pulse" />
          <h2 className="text-sm font-bold text-white tracking-wide">Important for You</h2>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
            {signals.length} ACTIVE
          </span>
        </div>

        <span className="text-[10px] text-slate-500 font-mono">PROACTIVE KNOWLEDGE</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {signals.map((sig) => (
          <div
            key={sig.id}
            onClick={() => handleAskAboutSignal(sig)}
            className="group relative bg-slate-950/70 hover:bg-slate-900/90 border border-slate-800 hover:border-indigo-500/40 p-4 rounded-2xl transition-all cursor-pointer space-y-2 shadow-md"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-start space-x-2.5">
                {getSignalIcon(sig.signal_type, sig.priority)}
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[9px] font-mono font-bold uppercase text-indigo-400 tracking-wider">
                      {sig.signal_type.replace('_', ' ')}
                    </span>
                    {sig.priority === 'HIGH' && (
                      <span className="text-[8px] font-bold px-1.5 py-0.2 bg-rose-500/20 text-rose-300 rounded border border-rose-500/30">
                        HIGH
                      </span>
                    )}
                  </div>
                  <h4 className="text-xs font-bold text-slate-100 group-hover:text-indigo-300 transition-colors mt-0.5">
                    {sig.title}
                  </h4>
                </div>
              </div>

              <button
                type="button"
                onClick={(e) => handleDismiss(sig.id, e)}
                className="text-slate-500 hover:text-slate-300 p-1 rounded-lg hover:bg-slate-800 transition-colors"
                title="Dismiss"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            <p className="text-[11px] text-slate-300 leading-relaxed pl-6">
              {sig.summary}
            </p>

            <div className="flex items-center justify-between pt-1 pl-6 text-[10px]">
              <span className="text-slate-500 font-mono">{sig.created_at ? sig.created_at.slice(0, 10) : ''}</span>
              <span className="text-indigo-400 group-hover:translate-x-0.5 transition-transform flex items-center space-x-1 font-medium">
                <span>Ask MindMesh</span>
                <ArrowRight className="w-3 h-3" />
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
