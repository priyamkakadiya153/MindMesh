import React, { useState, useEffect } from 'react';
import {
  askAssistant, conductTopicResearch, generateActionPreview,
  AskAssistantResponse, ResearchWorkspaceResponse, ActionPreviewResponse
} from '../contextual-assistant-api';
import {
  Bot, Sparkles, Send, BookOpen, Layers, ShieldCheck, CheckCircle2, AlertTriangle, ArrowRight, CornerDownRight, RefreshCw, FileText, Check
} from 'lucide-react';

interface ContextualAssistantPanelProps {
  initialEntityId?: string;
  initialEntityType?: string;
  initialProjectId?: string;
  token?: string;
}

export const ContextualAssistantPanel: React.FC<ContextualAssistantPanelProps> = ({
  initialEntityId = 'doc-auth-v2',
  initialEntityType = 'DOCUMENT',
  initialProjectId = 'proj-auth-101',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'ASK' | 'RESEARCH'>('ASK');
  const [question, setQuestion] = useState<string>('What is the current JWT expiry configuration?');
  const [askResult, setAskResult] = useState<AskAssistantResponse | null>(null);
  const [researchTopic, setResearchTopic] = useState<string>('Authentication Architecture');
  const [researchResult, setResearchResult] = useState<ResearchWorkspaceResponse | null>(null);
  const [actionPreview, setActionPreview] = useState<ActionPreviewResponse | null>(null);
  const [actionConfirmed, setActionConfirmed] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleAsk = async (q: string = question) => {
    if (!q.trim()) return;
    setIsLoading(true);
    try {
      const res = await askAssistant(q, initialEntityId, initialEntityType, initialProjectId, undefined, token);
      setAskResult(res);
    } catch (err) {
      console.error('Failed ask assistant:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResearch = async () => {
    if (!researchTopic.trim()) return;
    setIsLoading(true);
    try {
      const res = await conductTopicResearch(researchTopic, initialProjectId, token);
      setResearchResult(res);
    } catch (err) {
      console.error('Failed research:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    handleAsk();
  }, [initialEntityId, initialEntityType, token]);

  const handleRequestAction = async (title: string) => {
    try {
      const act = await generateActionPreview('CREATE_TASK', title, initialProjectId, token);
      setActionPreview(act);
      setActionConfirmed(false);
    } catch (err) {
      console.error('Failed action preview:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2.5 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                CONTEXTUAL AI ASSISTANT & KNOWLEDGE COPILOT
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Zero Hallucination & Prompt Isolation</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Bot className="w-7 h-7 text-indigo-400" />
              <span>Ask MindMesh Contextual Assistant</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Operates on authorized organizational memory, current entity context, graph relationships, and governed knowledge.
            </p>
          </div>

          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('ASK')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all flex items-center space-x-1 ${
                activeTab === 'ASK' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Bot className="w-3.5 h-3.5" />
              <span>Ask MindMesh</span>
            </button>
            <button
              type="button"
              onClick={() => { setActiveTab('RESEARCH'); handleResearch(); }}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all flex items-center space-x-1 ${
                activeTab === 'RESEARCH' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Research Workspace</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Mode View */}
      {activeTab === 'ASK' ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Left 2 Cols: Question Box & Answer Stream */}
          <div className="md:col-span-2 space-y-5">
            
            {/* Input Box */}
            <div className="bg-slate-900/80 border border-indigo-800/60 p-4 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center space-x-2 bg-slate-950 border border-slate-800 rounded-2xl px-4 py-2.5">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
                  placeholder="Ask a contextual question (e.g. 'Why did we choose PostgreSQL?' or 'What changed?')"
                  className="w-full bg-transparent text-xs text-white focus:outline-none placeholder-slate-500 font-medium"
                />
                <button
                  type="button"
                  onClick={() => handleAsk()}
                  className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1 flex-shrink-0"
                >
                  <Send className="w-3 h-3" />
                  <span>Ask</span>
                </button>
              </div>
            </div>

            {/* Source Grounded Answer Card */}
            {askResult && (
              <div className="bg-slate-900/80 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center space-x-2">
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                    <span className="text-xs font-bold text-white">Source-Grounded Answer</span>
                  </div>
                  <span className="text-[9px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60">
                    Confidence: {askResult.confidence_label}
                  </span>
                </div>

                {askResult.has_conflict && (
                  <div className="p-3 bg-amber-950/40 border border-amber-800/60 rounded-xl text-xs text-amber-200 flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    <span>{askResult.conflict_summary}</span>
                  </div>
                )}

                <p className="text-xs text-slate-200 leading-relaxed font-medium bg-slate-950 p-4 rounded-2xl border border-slate-800">
                  {askResult.answer}
                </p>

                {/* Follow-up Prompts */}
                <div className="space-y-1.5">
                  <span className="text-[9px] font-mono text-slate-500 uppercase block">Suggested Follow-ups</span>
                  <div className="flex flex-wrap gap-2">
                    {askResult.suggested_followups.map((f, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => { setQuestion(f); handleAsk(f); }}
                        className="px-3 py-1 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl text-[10px] text-indigo-400 font-bold transition-all"
                      >
                        • {f}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

          </div>

          {/* Right Col: Primary Source Panel & Action Preview Drawer */}
          <div className="space-y-4">
            
            {/* Primary Source Panel */}
            {askResult && (
              <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
                <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                  <FileText className="w-4 h-4 text-indigo-400" />
                  <h4 className="text-xs font-bold text-white">Grounded Primary Sources ({askResult.sources.length})</h4>
                </div>

                <div className="space-y-2 text-xs">
                  {askResult.sources.map((s) => (
                    <div key={s.entity_id} className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-[8px] font-mono font-bold text-indigo-400 bg-slate-900 px-1.5 py-0.5 rounded">{s.entity_type}</span>
                        <span className="text-[8px] font-mono text-emerald-400">{s.status}</span>
                      </div>
                      <h5 className="font-bold text-slate-100 text-[11px]">{s.name}</h5>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Action Preview Modal */}
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <h4 className="text-xs font-bold text-white">Recommended Action Orchestration</h4>
              <button
                type="button"
                onClick={() => handleRequestAction('Update deployment environment variable checklist')}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs shadow-md transition-all"
              >
                Request Task Action
              </button>

              {actionPreview && (
                <div className="p-3 bg-slate-950 border border-indigo-800/60 rounded-xl space-y-2 text-xs">
                  <span className="text-[9px] font-mono font-bold text-indigo-400 uppercase">Action Preview</span>
                  <p className="text-[11px] text-slate-200">{actionPreview.expected_change}</p>

                  {!actionConfirmed ? (
                    <button
                      type="button"
                      onClick={() => setActionConfirmed(true)}
                      className="w-full py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs"
                    >
                      Confirm Action Execution
                    </button>
                  ) : (
                    <div className="p-2 bg-emerald-950 border border-emerald-800/60 rounded-xl text-emerald-400 text-[10px] font-mono flex items-center space-x-1">
                      <Check className="w-3.5 h-3.5" />
                      <span>Action Confirmed & Executed via Phase 5.1!</span>
                    </div>
                  )}
                </div>
              )}
            </div>

          </div>

        </div>
      ) : (
        /* Research Mode Workspace */
        researchResult && (
          <div className="bg-slate-900/80 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-xs font-bold text-white flex items-center space-x-2">
                <BookOpen className="w-4 h-4 text-indigo-400" />
                <span>Topic Research Synthesis: {researchResult.topic}</span>
              </h3>
            </div>

            <p className="text-xs text-slate-300 font-medium">{researchResult.summary}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
                <span className="text-[9px] font-mono font-bold text-indigo-400 uppercase block">Key Findings</span>
                {researchResult.findings.map((f, i) => (
                  <p key={i} className="text-xs text-slate-300">• {f}</p>
                ))}
              </div>

              <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
                <span className="text-[9px] font-mono font-bold text-amber-400 uppercase block">Open Questions</span>
                {researchResult.open_questions.map((q, i) => (
                  <p key={i} className="text-xs text-slate-300">❓ {q}</p>
                ))}
              </div>
            </div>
          </div>
        )
      )}

    </div>
  );
};
