import React from 'react';
import { FileSearch, Sparkles, BookOpen, Layers, Search, Bot, MessageSquare, ArrowRight, Zap } from 'lucide-react';

interface SuggestedQuestionsProps {
  onSelectQuestion: (question: string) => void;
}

const SUGGESTED_ITEMS = [
  {
    icon: FileSearch,
    title: "Ask about uploaded documents",
    desc: "Extract key metrics, clauses, and summaries from indexed PDFs & Markdown files."
  },
  {
    icon: Sparkles,
    title: "Summarize this workspace",
    desc: "Generate an executive summary of current workspace milestones and project status."
  },
  {
    icon: BookOpen,
    title: "Find meeting decisions",
    desc: "Retrieve key action items and decisions made in recent team discussions."
  },
  {
    icon: Layers,
    title: "Explain system architecture",
    desc: "Unpack system architecture specifications and design system principles."
  }
];

export const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({ onSelectQuestion }) => {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 md:p-10 max-w-4xl mx-auto my-auto text-center overflow-y-auto custom-scrollbar">
      {/* Welcome Header */}
      <div className="space-y-4 mb-8 max-w-xl">
        <div className="relative inline-flex items-center justify-center">
          <div className="h-14 w-14 rounded-2xl bg-accentSubtle border border-accent/30 text-accentText flex items-center justify-center shadow-lg shadow-accent/10">
            <Bot size={28} />
          </div>
          <span className="absolute -top-1 -right-1 flex h-4 w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
            <span className="relative inline-flex rounded-full h-4 w-4 bg-accent"></span>
          </span>
        </div>

        <div className="space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-accentSubtle/60 border border-accent/20 rounded-full text-[11px] font-semibold text-accentText">
            <Zap size={12} /> MindMesh Intelligence Engine
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-textPrimary">
            How can I assist your workspace today?
          </h2>
          <p className="text-xs sm:text-sm text-textMuted leading-relaxed max-w-lg mx-auto">
            Ask questions, analyze uploaded documents, summarize team discussions, or discover organizational decisions grounded in real-time knowledge.
          </p>
        </div>
      </div>

      {/* Suggestion Cards Grid (Equal height and width) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full max-w-2xl mb-8">
        {SUGGESTED_ITEMS.map((item, idx) => {
          const Icon = item.icon;
          return (
            <button
              key={idx}
              onClick={() => onSelectQuestion(item.title)}
              className="flex flex-col justify-between p-4 bg-bgCard hover:bg-bgHover border border-borderColor hover:border-accent/40 rounded-2xl text-left transition-all duration-200 hover:-translate-y-0.5 active:scale-[0.99] group shadow-sm hover:shadow-md h-full min-h-[100px]"
            >
              <div className="flex items-start gap-3">
                <div className="p-2 bg-accentSubtle/80 text-accentText border border-accent/20 rounded-xl group-hover:bg-accent group-hover:text-white transition-colors shrink-0">
                  <Icon size={16} />
                </div>
                <div className="space-y-1 min-w-0 flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold text-textPrimary group-hover:text-accentText transition-colors truncate">
                      {item.title}
                    </h4>
                    <ArrowRight size={13} className="text-textMuted group-hover:text-accentText group-hover:translate-x-0.5 transition-all shrink-0 ml-1" />
                  </div>
                  <p className="text-[11px] text-textMuted leading-relaxed line-clamp-2">
                    {item.desc}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Quick Prompt Chips */}
      <div className="flex flex-wrap items-center justify-center gap-2 max-w-xl text-xs text-textMuted">
        <span className="text-[10px] font-bold uppercase tracking-wider text-textMuted">Try asking:</span>
        {[
          "What are our Q3 milestones?",
          "Summarize recent architectural decisions",
          "Extract file metadata"
        ].map((prompt, pIdx) => (
          <button
            key={pIdx}
            onClick={() => onSelectQuestion(prompt)}
            className="px-3 py-1 bg-bgInput hover:bg-bgHover border border-borderColor hover:border-accent/30 rounded-full text-[11px] text-textSecondary hover:text-textPrimary transition-colors active:scale-95"
          >
            "{prompt}"
          </button>
        ))}
      </div>
    </div>
  );
};

