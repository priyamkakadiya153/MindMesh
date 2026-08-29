import React, { useState, useEffect } from 'react';
import {
  executeSynthesis, fetchSynthesisModes, SynthesisResponse, SynthesisModeItem
} from '../synthesis-engine-api';
import {
  BrainCircuit, Search, Sparkles, Layers, ShieldCheck, AlertCircle, FileText, CheckSquare, MessageSquare, ArrowRight, Activity, CornerDownRight, RefreshCw
} from 'lucide-react';

interface KnowledgeSynthesisCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const KnowledgeSynthesisCenter: React.FC<KnowledgeSynthesisCenterProps> = ({
  initialProjectId = 'proj-auth-id',
  token
}) => {
  const [query, setQuery] = useState<string>('What is the current state of Authentication?');
  const [selectedMode, setSelectedMode] = useState<string>('OVERVIEW');
  const [modes, setModes] = useState<SynthesisModeItem[]>([]);
  const [synthesisData, setSynthesisData] = useState<SynthesisResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadModes = async () => {
    try {
      const res = await fetchSynthesisModes(token);
      setModes(res);
    } catch (err) {
      console.error('Failed to load synthesis modes:', err);
    }
  };

  useEffect(() => {
    loadModes();
  }, [token]);

  const handleSynthesize = async () => {
    if (!query.strip && !query) return;
    setIsLoading(true);
    try {
      const res = await executeSynthesis(query, selectedMode, initialProjectId, token);
      setSynthesisData(res);
    } catch (err) {
      console.error('Failed to synthesize:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                KNOWLEDGE SYNTHESIS & ORGANIZATIONAL MEMORY
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <BrainCircuit className="w-7 h-7 text-indigo-400" />
              <span>Knowledge Synthesis Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Synthesize cross-source organizational memory (Conversations, Decisions, Documents, Tasks, Graph, Timeline) into structured, evidence-backed understanding.
            </p>
          </div>
        </div>

        {/* Input Query Bar & Mode Selector */}
        <div className="space-y-3 pt-3 border-t border-slate-800/80">
          <div className="flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSynthesize()}
                placeholder="Ask MindMesh to synthesize knowledge (e.g. 'What is the current state of Authentication?')"
                className="w-full bg-slate-950 border border-slate-800 rounded-2xl pl-9 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-medium"
              />
            </div>
            <button
              type="button"
              onClick={handleSynthesize}
              disabled={isLoading}
              className="px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center space-x-1.5 flex-shrink-0 disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isLoading ? 'Synthesizing...' : 'Synthesize'}</span>
            </button>
          </div>

          {/* Modes Pills */}
          <div className="flex flex-wrap gap-2 pt-1">
            {modes.map((m) => (
              <button
                key={m.mode}
                type="button"
                onClick={() => setSelectedMode(m.mode)}
                className={`px-3 py-1 rounded-xl text-[11px] font-bold font-mono transition-all ${
                  selectedMode === m.mode
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                {m.mode}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Results Split */}
      {synthesisData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Left 2 Cols: Structured Synthesis Output */}
          <div className="md:col-span-2 space-y-4">
            
            <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-5 backdrop-blur-md">
              
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-mono font-bold text-indigo-400 bg-indigo-950 px-2.5 py-0.5 rounded border border-indigo-800/60 uppercase">
                    Mode: {synthesisData.mode}
                  </span>
                  <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2.5 py-0.5 rounded border border-emerald-800/60 uppercase">
                    Confidence: {synthesisData.confidence}
                  </span>
                </div>
              </div>

              {/* Structured Sections */}
              <div className="space-y-4">
                
                {/* Current State */}
                <div className="p-4 bg-slate-950 border border-indigo-900/40 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono font-bold text-indigo-400 uppercase">CURRENT STATE</span>
                  <p className="text-xs font-bold text-white leading-relaxed">{synthesisData.structured_answer.current_state}</p>
                </div>

                {/* Why */}
                <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono font-bold text-slate-400 uppercase">WHY & RATIONALE</span>
                  <p className="text-xs text-slate-300 leading-relaxed">{synthesisData.structured_answer.why}</p>
                </div>

                {/* Open Work */}
                <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono font-bold text-amber-400 uppercase">OPEN WORK & BLOCKERS</span>
                  <p className="text-xs text-slate-300 leading-relaxed">{synthesisData.structured_answer.open_work}</p>
                </div>

                {/* Conflicts */}
                <div className="p-4 bg-slate-950 border border-rose-900/40 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono font-bold text-rose-400 uppercase">CONFLICTS & GOVERNANCE WARNS</span>
                  <p className="text-xs text-slate-300 leading-relaxed">{synthesisData.structured_answer.conflicts}</p>
                </div>

              </div>

            </div>

          </div>

          {/* Right Col: Evidence Sources & Suggested Actions */}
          <div className="space-y-4">
            
            {/* Citations Card */}
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <h4 className="text-xs font-bold text-white">Supporting Sources ({synthesisData.sources.length})</h4>
              </div>

              <div className="space-y-2">
                {synthesisData.sources.map((src) => (
                  <div key={src.id} className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="text-[8px] font-mono font-bold text-indigo-400 bg-slate-900 px-1.5 py-0.2 rounded uppercase">
                        {src.type}
                      </span>
                      <span className={`text-[8px] font-mono font-bold px-1.5 py-0.2 rounded uppercase ${
                        src.status === 'CURRENT' ? 'text-emerald-400 bg-emerald-950' : 'text-amber-400 bg-amber-950'
                      }`}>
                        {src.status}
                      </span>
                    </div>
                    <h5 className="font-bold text-slate-200 text-[11px]">{src.title}</h5>
                    <p className="text-[9px] font-mono text-slate-500">{src.citation}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Suggested Actions Card */}
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <h4 className="text-xs font-bold text-white border-b border-slate-800 pb-2">Suggested Actions</h4>
              <div className="space-y-2">
                {synthesisData.suggested_actions.map((act, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="w-full text-left p-2.5 bg-slate-950 hover:bg-slate-900 border border-slate-800 rounded-xl text-xs font-bold text-indigo-300 transition-all flex items-center justify-between"
                  >
                    <span>{act}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  </button>
                ))}
              </div>
            </div>

          </div>

        </div>
      )}

    </div>
  );
};
