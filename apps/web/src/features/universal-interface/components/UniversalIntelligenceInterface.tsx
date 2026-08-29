import React, { useState, useEffect } from 'react';
import {
  queryUniversalInterface, fetchFileIntelligence, convertAnswerToAction, fetchAvailableContextSources,
  UniversalAnswerResponse, FileIntelligenceResponse, ContextSourcesResponse
} from '../universal-interface-api';
import {
  Search, Compass, Cpu, FileText, CheckCircle2, Shield, ArrowRight, Layers, HelpCircle, Activity, Sparkles, ExternalLink
} from 'lucide-react';

interface UniversalIntelligenceInterfaceProps {
  initialResourceId?: string;
  token?: string;
}

export const UniversalIntelligenceInterface: React.FC<UniversalIntelligenceInterfaceProps> = ({
  initialResourceId,
  token
}) => {
  const [promptInput, setPromptInput] = useState<string>('What is currently blocking Project Alpha?');
  const [answer, setAnswer] = useState<UniversalAnswerResponse | null>(null);
  const [fileIntel, setFileIntel] = useState<FileIntelligenceResponse | null>(null);
  const [contextSources, setContextSources] = useState<ContextSourcesResponse | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const sourcesRes = await fetchAvailableContextSources(token);
      setContextSources(sourcesRes);
    } catch (err) {
      console.error('Failed to load context sources:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const handleQuery = async () => {
    if (!promptInput.trim()) return;
    setIsLoading(true);
    try {
      const res = await queryUniversalInterface(promptInput, initialResourceId, token);
      setAnswer(res);
      setActionMessage(`Intent: ${res.intent_type} | Scope: ${res.scope} | Grounded Answer Ready`);
    } catch (err) {
      console.error('Query failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInspectDstFile = async () => {
    setIsLoading(true);
    try {
      const res = await fetchFileIntelligence('embroidery_design.dst', 'application/x-tajima', token);
      setFileIntel(res);
      setActionMessage(`File Intelligence Analyzed: ${res.file_type}`);
    } catch (err) {
      console.error('File intelligence failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleActionHandoff = async (actionType: string, payload: Record<string, any>) => {
    try {
      const res = await convertAnswerToAction(actionType, payload, token);
      setActionMessage(`Phase 6.21 Action Plan Created: ID '${res.created_plan_id}' (Human Approval Gate Enforced)`);
    } catch (err) {
      console.error('Action handoff failed:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2.5 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                UNIVERSAL KNOWLEDGE INTERFACE & OPERATING LAYER
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <Sparkles className="w-3 h-3" />
                <span>Zero Navigation Friction</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Compass className="w-7 h-7 text-indigo-400" />
              <span>Universal Intelligence Operating Interface</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Express any intent naturally. MindMesh orchestrates search, evidence, files, decisions, and Phase 6.21 action execution seamlessly.
            </p>
          </div>

          {/* Quick DST File Test Button */}
          <button
            type="button"
            onClick={handleInspectDstFile}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl font-mono text-xs font-bold text-white shadow-lg flex items-center space-x-2 flex-shrink-0"
          >
            <FileText className="w-4 h-4" />
            <span>Test DST File Intelligence</span>
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-indigo-950/80 border border-indigo-800/60 rounded-2xl text-xs text-indigo-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-indigo-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Universal Command Bar */}
      <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex items-center space-x-3 bg-slate-950 border border-slate-800 rounded-2xl p-2.5 shadow-inner">
          <Search className="w-5 h-5 text-indigo-400 ml-2" />
          <input
            type="text"
            value={promptInput}
            onChange={(e) => setPromptInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
            className="w-full bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none"
            placeholder="Ask a question, search knowledge, compare files, or request action..."
          />
          <button
            type="button"
            onClick={handleQuery}
            disabled={isLoading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold text-xs flex items-center space-x-1 flex-shrink-0"
          >
            <span>Ask MindMesh</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {contextSources && (
          <div className="flex items-center space-x-3 overflow-x-auto text-[11px] font-mono text-slate-400 pt-1">
            <span className="text-slate-500 font-bold uppercase text-[9px]">Active Scopes:</span>
            {contextSources.available_scopes.map(s => (
              <span key={s.scope} className="bg-slate-950 px-2.5 py-1 rounded-xl border border-slate-800/80 whitespace-nowrap">
                {s.label} ({s.count})
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Multi-Source Answer Card */}
      {answer && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-[9px] font-mono font-bold text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800/60 uppercase">{answer.intent_type} INTENT</span>
              <span className="text-[9px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 uppercase">{answer.confidence} CONFIDENCE</span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">Freshness: {new Date(answer.freshness_timestamp).toLocaleTimeString()}</span>
          </div>

          {/* Answer Text */}
          <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl text-sm text-slate-200 leading-relaxed">
            {answer.answer_text}
          </div>

          {/* Evidence Panel */}
          <div className="space-y-3">
            <span className="text-xs font-bold text-white font-mono uppercase block">Grounding Evidence & Sources</span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {answer.evidence.map((ev, idx) => (
                <div key={idx} className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-indigo-400">{ev.source_type}: {ev.title}</span>
                    <span className="text-[9px] font-mono text-slate-400 font-bold">{(ev.authority_score * 100).toFixed(0)}% Score</span>
                  </div>
                  <p className="text-slate-300 text-xs">{ev.snippet}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Recommended Action Handoff */}
          {answer.recommended_actions.length > 0 && (
            <div className="space-y-3 pt-2">
              <span className="text-xs font-bold text-white font-mono uppercase block">Actionable Handoff (Phase 6.21 Execution Gate)</span>
              <div className="flex flex-wrap gap-3">
                {answer.recommended_actions.map((act, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleActionHandoff(act.action_type, act.payload)}
                    className="px-4 py-2 bg-emerald-950 hover:bg-emerald-900 border border-emerald-800/60 rounded-xl font-bold text-xs text-emerald-300 flex items-center space-x-1.5"
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>{act.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* DST File Intelligence View */}
      {fileIntel && (
        <div className="bg-slate-900/80 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <span className="font-mono font-bold text-xs text-indigo-400 uppercase">DST File Intelligence (Native Preview Handling)</span>
            <span className="text-[9px] font-mono text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 font-bold">NO FAKE PREVIEW</span>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
            <p className="text-slate-300">• <strong className="text-white">File:</strong> {fileIntel.file_name} ({fileIntel.file_type})</p>
            <p className="text-amber-300 text-[11px]">• {fileIntel.preview_explanation}</p>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
            <span className="font-bold text-white block font-mono">Extracted Embroidery Parameters</span>
            <p className="text-slate-300">• Stitch Count: <strong>{fileIntel.extracted_intelligence.stitch_count}</strong></p>
            <p className="text-slate-300">• Color Changes: <strong>{fileIntel.extracted_intelligence.color_changes}</strong></p>
            <p className="text-slate-300">• Dimensions: <strong>{fileIntel.extracted_intelligence.dimensions_mm}</strong></p>
          </div>
        </div>
      )}

    </div>
  );
};
