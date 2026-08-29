import React from 'react';
import { Bot, Lightbulb, Sparkles, AlertCircle } from 'lucide-react';

import { AIInsightsSkeleton, WidgetErrorCard } from './Skeletons';

interface AIInsightsProps {
  insights?: string;
  status?: string;
  onNavigateToChat: () => void;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export function AIInsights({
  insights = 'No AI insights generated yet. Add documents or start a conversation to begin.',
  status = 'idle',
  onNavigateToChat,
  loading,
  error,
  onRetry
}: AIInsightsProps) {
  if (error) {
    return <WidgetErrorCard title="Unable to load AI Insights" message={error} onRetry={onRetry} />;
  }

  if (loading) {
    return <AIInsightsSkeleton />;
  }
  const suggestions = [
    'Analyze knowledge base documents schema',
    'Summarize discussion about multitenancy authentication',
    'Extract milestones and checklist items for projects'
  ];

  const isActive = status === 'active';

  return (
    <div className="glass-panel p-3.5 bg-bgCard border border-borderColor flex flex-col justify-between h-full rounded-2xl">
      <div>
        <div className="flex items-center justify-between mb-2.5 pb-1.5 border-b border-borderMuted">
          <h2 className="text-xs font-semibold text-textPrimary tracking-wide flex items-center gap-2">
            <Bot size={15} className="text-accentText" aria-hidden="true" />
            <span>AI Knowledge Insights</span>
          </h2>
          <span className={`flex items-center gap-1.5 text-[9px] px-2 py-0.5 rounded-full font-medium ${
            isActive ? 'bg-successBg text-successText' : 'bg-bgTertiary text-textMuted'
          }`}>
            <span className={`h-1.5 w-1.5 rounded-full ${isActive ? 'bg-successText animate-pulse' : 'bg-textMuted'}`} aria-hidden="true" />
            {isActive ? 'Active' : 'Idle'}
          </span>
        </div>

        <div className="space-y-2.5">
          <div className="p-2.5 bg-accentSubtle border border-accent/20 rounded-xl">
            <div className="flex gap-2 items-start text-xs">
              <Lightbulb size={15} className="text-amber-500 shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <h3 className="font-semibold text-textPrimary text-xs">Personalized Briefing</h3>
                <p className="text-textSecondary mt-0.5 leading-relaxed text-[10px]">{insights}</p>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-[9px] text-textMuted uppercase tracking-widest font-semibold mb-1.5">Suggested Queries</h3>
            <div className="space-y-1">
              {suggestions.map((sug, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={onNavigateToChat}
                  aria-label={`Ask AI: ${sug}`}
                  title={sug}
                  className="w-full text-left p-2 bg-bgTertiary hover:bg-bgHover border border-borderMuted hover:border-accent/20 rounded-lg text-[10px] text-textSecondary hover:text-textPrimary transition-all flex items-center gap-2 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                >
                  <Sparkles size={10} className="text-accentText group-hover:scale-110 transition-transform" aria-hidden="true" />
                  <span className="truncate">{sug}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={onNavigateToChat}
        className="mt-3 w-full py-1.5 bg-accent hover:bg-accentHover text-white text-xs font-bold rounded-xl border border-accent/20 flex items-center justify-center gap-1.5 shadow-lg shadow-accent/10 transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        <Bot size={13} aria-hidden="true" />
        <span>Ask AI Assistant</span>
      </button>
    </div>
  );
}
