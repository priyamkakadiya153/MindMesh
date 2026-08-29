import React, { useState, useEffect } from 'react';
import {
  fetchConversationSummary, fetchConversationKnowledge, generateMeetingNotes, promoteItemToProject,
  ConversationSummaryResponse, ExtractedKnowledgeItem, MeetingNotesResponse
} from '../conversation-intelligence-api';
import {
  MessageSquare, Sparkles, CheckCircle2, HelpCircle, AlertTriangle, FileText, Clock, ArrowRight, ExternalLink, Share2, Check, X
} from 'lucide-react';

interface ConversationKnowledgePanelProps {
  chatId: string;
  projectId?: string;
  token?: string;
}

export const ConversationKnowledgePanel: React.FC<ConversationKnowledgePanelProps> = ({
  chatId,
  projectId,
  token
}) => {
  const [summary, setSummary] = useState<ConversationSummaryResponse | null>(null);
  const [items, setItems] = useState<ExtractedKnowledgeItem[]>([]);
  const [meetingNotes, setMeetingNotes] = useState<MeetingNotesResponse | null>(null);
  const [summaryType, setSummaryType] = useState<'QUICK' | 'DETAILED' | 'ACTION'>('QUICK');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [sumRes, knowRes] = await Promise.all([
          fetchConversationSummary(chatId, summaryType, token),
          fetchConversationKnowledge(chatId, token)
        ]);
        setSummary(sumRes);
        setItems(knowRes);
      } catch (err) {
        console.error('Failed to load conversation intelligence:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, [chatId, summaryType, token]);

  const handleGenerateNotes = async () => {
    try {
      const res = await generateMeetingNotes(chatId, undefined, token);
      setMeetingNotes(res);
    } catch (err) {
      console.error('Failed to generate meeting notes:', err);
    }
  };

  const handlePromote = async (itemId: string) => {
    if (!projectId) return;
    try {
      await promoteItemToProject(chatId, itemId, projectId, token);
      setItems((prev) => prev.map((i) => i.id === itemId ? { ...i, status: 'CONFIRMED' } : i));
    } catch (err) {
      console.error('Failed to promote item:', err);
    }
  };

  return (
    <div className="w-full bg-slate-900/80 border border-slate-800 p-5 rounded-3xl space-y-5 font-sans text-xs shadow-xl backdrop-blur-md">
      
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <MessageSquare className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-bold text-white">Conversation Intelligence</h3>
        </div>

        <button
          type="button"
          onClick={handleGenerateNotes}
          className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[11px] shadow-md transition-all flex items-center space-x-1"
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Generate Meeting Notes</span>
        </button>
      </div>

      {/* Summary Section */}
      {summary && (
        <div className="space-y-3 bg-slate-950/70 p-4 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-[9px] font-mono font-bold uppercase text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded">
              {summary.summary_type} SUMMARY
            </span>
            
            <div className="flex items-center space-x-1">
              {(['QUICK', 'DETAILED', 'ACTION'] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setSummaryType(t)}
                  className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold ${
                    summaryType === t ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <p className="text-slate-200 text-xs leading-relaxed">{summary.summary_text}</p>

          {/* Topics */}
          <div className="flex flex-wrap gap-1.5 pt-1">
            {summary.topics.map((tp, idx) => (
              <span key={idx} className="text-[9px] font-mono px-2 py-0.5 bg-slate-900 text-slate-300 rounded border border-slate-800">
                #{tp}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Extracted Knowledge Items */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold text-slate-300">Extracted Decisions & Action Items</h4>

        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
          {items.map((item) => (
            <div key={item.id} className="p-3 bg-slate-950/70 border border-slate-800 rounded-2xl flex items-center justify-between text-xs">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                    item.item_type === 'DECISION'
                      ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60'
                      : item.item_type === 'TASK'
                      ? 'bg-indigo-950 text-indigo-400 border-indigo-800/60'
                      : 'bg-amber-950 text-amber-400 border-amber-800/60'
                  }`}>
                    {item.item_type}
                  </span>
                  <h5 className="font-bold text-slate-200">{item.title}</h5>
                </div>
                <p className="text-[11px] text-slate-400">{item.description}</p>
              </div>

              {projectId && item.status !== 'CONFIRMED' && (
                <button
                  type="button"
                  onClick={() => handlePromote(item.id)}
                  className="px-2.5 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-indigo-400 font-bold text-[10px] flex items-center space-x-1"
                >
                  <Share2 className="w-3 h-3" />
                  <span>Promote</span>
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Generated Meeting Notes Modal */}
      {meetingNotes && (
        <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-2">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="font-bold text-white text-xs">{meetingNotes.title}</h4>
            <button
              type="button"
              onClick={() => setMeetingNotes(null)}
              className="text-slate-500 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <pre className="text-[11px] text-slate-300 whitespace-pre-wrap font-sans bg-slate-900 p-3 rounded-xl border border-slate-800 max-h-48 overflow-y-auto">
            {meetingNotes.notes_markdown}
          </pre>
        </div>
      )}

    </div>
  );
};
