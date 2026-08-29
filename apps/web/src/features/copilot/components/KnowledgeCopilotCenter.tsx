import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { askKnowledgeCopilot, fetchProjectBrief, CopilotAnswerResponse, ProjectBriefResponse } from '../copilot-api';
import {
  BrainCircuit, Sparkles, AlertTriangle, CheckCircle2, ShieldAlert, ArrowRight, ExternalLink, Network, RefreshCw, FileText, Send, HelpCircle
} from 'lucide-react';

interface KnowledgeCopilotCenterProps {
  workspaceId?: string;
  projectId?: string;
  token?: string;
}

export const KnowledgeCopilotCenter: React.FC<KnowledgeCopilotCenterProps> = ({
  workspaceId,
  projectId,
  token
}) => {
  const navigate = useNavigate();
  const [question, setQuestion] = useState<string>('Why did we choose PostgreSQL?');
  const [copilotResponse, setCopilotResponse] = useState<CopilotAnswerResponse | null>(null);
  const [projectBrief, setProjectBrief] = useState<ProjectBriefResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleAsk = async (qText: string) => {
    if (!qText.trim()) return;
    setIsLoading(true);
    try {
      const res = await askKnowledgeCopilot(qText, workspaceId, projectId, token);
      setCopilotResponse(res);
      setProjectBrief(null);
    } catch (err) {
      console.error('Failed to ask copilot:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFetchBrief = async () => {
    if (!projectId) return;
    setIsLoading(true);
    try {
      const res = await fetchProjectBrief(projectId, token);
      setProjectBrief(res);
      setCopilotResponse(null);
    } catch (err) {
      console.error('Failed to generate project brief:', err);
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
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
              MINDSMESH KNOWLEDGE COPILOT
            </span>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <BrainCircuit className="w-7 h-7 text-indigo-400" />
              <span>Grounded Answer Engine</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Ask questions directly to your organizational memory. Every response is strictly grounded in retrieved evidence with exact source citations.
            </p>
          </div>

          {projectId && (
            <button
              type="button"
              onClick={handleFetchBrief}
              className="px-4 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg transition-all flex items-center space-x-1.5"
            >
              <FileText className="w-4 h-4" />
              <span>Generate Project Brief</span>
            </button>
          )}
        </div>

        {/* Question Input */}
        <div className="relative">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAsk(question)}
            placeholder="Ask MindMesh (e.g. 'Why did we choose PostgreSQL?', 'What is blocking authentication?')..."
            className="w-full bg-slate-950/80 border border-slate-800 pl-4 pr-24 py-3.5 rounded-2xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 shadow-inner"
          />

          <button
            type="button"
            onClick={() => handleAsk(question)}
            className="absolute right-2 top-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md flex items-center space-x-1"
          >
            <span>Ask</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Sample Question Pills */}
        <div className="flex flex-wrap gap-2 pt-1">
          {[
            'Why did we choose PostgreSQL?',
            'What was decided about JWT expiry?',
            'What tasks are currently blocked?',
            'How do we deploy authentication?'
          ].map((sample, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuestion(sample);
                handleAsk(sample);
              }}
              className="text-[10px] font-mono text-slate-400 bg-slate-950 hover:bg-slate-800 px-2.5 py-1 rounded-xl border border-slate-800 transition-all"
            >
              {sample}
            </button>
          ))}
        </div>
      </div>

      {/* Answer Output View */}
      {copilotResponse && (
        <div className="space-y-4 bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl backdrop-blur-md">
          
          {/* Answer Metadata Header */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <span className="text-[9px] font-mono font-bold uppercase px-2 py-0.5 bg-indigo-950 text-indigo-400 rounded border border-indigo-800/60">
                INTENT: {copilotResponse.intent}
              </span>

              <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                copilotResponse.confidence_state === 'Well supported'
                  ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60'
                  : copilotResponse.confidence_state === 'Conflicting evidence'
                  ? 'bg-amber-950 text-amber-400 border-amber-800/60'
                  : 'bg-rose-950 text-rose-400 border-rose-800/60'
              }`}>
                {copilotResponse.confidence_state}
              </span>
            </div>

            <span className="text-[10px] text-slate-500 font-mono">MindMesh Grounded Engine</span>
          </div>

          {/* Conflict Alert Warning */}
          {copilotResponse.conflict_warning && (
            <div className="p-3 bg-amber-950/60 border border-amber-800/60 rounded-2xl flex items-center space-x-2 text-amber-300 text-xs">
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span>{copilotResponse.conflict_warning}</span>
            </div>
          )}

          {/* Direct Answer */}
          <div className="space-y-2">
            <h3 className="text-sm font-bold text-slate-300">Direct Answer</h3>
            <p className="text-sm font-semibold text-white leading-relaxed bg-slate-950 p-4 rounded-2xl border border-slate-800 shadow-inner">
              {copilotResponse.direct_answer}
            </p>
          </div>

          {/* Key Supporting Points */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-300">Key Evidence Points</h4>
            <ul className="space-y-1.5 text-xs text-slate-300">
              {copilotResponse.key_points.map((pt, idx) => (
                <li key={idx} className="flex items-start space-x-2 bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/60">
                  <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 mt-0.5 flex-shrink-0" />
                  <span>{pt}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Exact Citations */}
          <div className="space-y-2 pt-2">
            <h4 className="text-xs font-bold text-slate-300">Sources & Grounded Citations</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {copilotResponse.citations.map((cit) => (
                <div key={cit.id} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-mono font-bold uppercase px-2 py-0.5 bg-slate-800 text-indigo-400 rounded">
                      {cit.entity_type}
                    </span>
                    <span className="text-[9px] text-slate-500">{cit.project_name}</span>
                  </div>
                  <h5 className="font-bold text-white text-xs">{cit.title}</h5>
                  <p className="text-[11px] text-slate-400 line-clamp-2">"{cit.excerpt}"</p>
                </div>
              ))}
            </div>
          </div>

          {/* Follow-up Contextual Questions */}
          {copilotResponse.follow_ups.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-800">
              <h4 className="text-xs font-bold text-slate-400">Suggested Follow-up Questions</h4>
              <div className="flex flex-wrap gap-2">
                {copilotResponse.follow_ups.map((f, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setQuestion(f);
                      handleAsk(f);
                    }}
                    className="text-[10px] font-mono text-indigo-300 bg-indigo-950/60 hover:bg-indigo-900/60 px-3 py-1 rounded-xl border border-indigo-800/60 transition-all flex items-center space-x-1"
                  >
                    <span>{f}</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                ))}
              </div>
            </div>
          )}

        </div>
      )}

      {/* Project Brief View */}
      {projectBrief && (
        <div className="space-y-4 bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl backdrop-blur-md font-sans">
          <div className="border-b border-slate-800 pb-3">
            <span className="text-[9px] font-mono font-bold uppercase text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded">
              PROJECT BRIEF
            </span>
            <h2 className="text-xl font-bold text-white mt-1">{projectBrief.project_name} Executive Brief</h2>
            <p className="text-xs text-slate-400">{projectBrief.overview}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-2">
              <h4 className="text-xs font-bold text-emerald-400">Key Decisions</h4>
              <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
                {projectBrief.key_decisions.map((d, idx) => <li key={idx}>{d}</li>)}
              </ul>
            </div>

            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-2">
              <h4 className="text-xs font-bold text-indigo-400">Open Tasks & Work</h4>
              <ul className="text-xs text-slate-300 space-y-1 list-disc list-inside">
                {projectBrief.open_tasks.map((t, idx) => <li key={idx}>{t}</li>)}
              </ul>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
