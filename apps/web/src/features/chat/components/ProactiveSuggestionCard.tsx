import React, { useState } from 'react';
import { Sparkles, Calendar, User, CheckSquare, Bell, X, Loader2 } from 'lucide-react';
import { ProactiveSuggestionItem } from '../../proactive-intelligence/proactive-detection-api';

interface ProactiveSuggestionCardProps {
  suggestion: ProactiveSuggestionItem;
  onPromoteTask: (suggestion: ProactiveSuggestionItem) => void;
  onPromoteReminder: (suggestion: ProactiveSuggestionItem) => void;
  onDismiss: (suggestionId: string) => void;
}

export const ProactiveSuggestionCard: React.FC<ProactiveSuggestionCardProps> = ({
  suggestion,
  onPromoteTask,
  onPromoteReminder,
  onDismiss
}) => {
  const [loading, setLoading] = useState(false);

  const handleTaskClick = async () => {
    setLoading(true);
    try {
      await onPromoteTask(suggestion);
    } finally {
      setLoading(false);
    }
  };

  const handleReminderClick = async () => {
    setLoading(true);
    try {
      await onPromoteReminder(suggestion);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="my-3 p-4 rounded-2xl bg-slate-900/90 border border-indigo-500/40 shadow-xl space-y-3 max-w-md animate-in fade-in slide-in-from-bottom-2 duration-200 select-none">
      {/* Header Badge */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <span>Potential action detected</span>
        </div>
        <button
          type="button"
          onClick={() => onDismiss(suggestion.id)}
          className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          title="Dismiss suggestion"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Main Content Title */}
      <div className="space-y-1">
        <h4 className="text-sm font-bold text-white leading-snug">{suggestion.title}</h4>
        {suggestion.deadline && (
          <div className="flex items-center gap-1.5 text-xs text-indigo-300 font-medium pt-0.5">
            <Calendar className="w-3.5 h-3.5 shrink-0 text-indigo-400" />
            <span>Deadline: <strong>{suggestion.deadline}</strong></span>
          </div>
        )}
        {suggestion.assignee_name && (
          <div className="flex items-center gap-1.5 text-xs text-slate-300 pt-0.5">
            <User className="w-3.5 h-3.5 shrink-0 text-slate-400" />
            <span>Assignee: <strong>{suggestion.assignee_name}</strong></span>
          </div>
        )}
      </div>

      {/* Source Provenance Label */}
      {suggestion.source_label && (
        <div className="text-[10px] text-slate-400 font-mono tracking-wide">
          {suggestion.source_label}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center gap-2 pt-1">
        <button
          type="button"
          onClick={handleTaskClick}
          disabled={loading}
          className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition-all disabled:opacity-50 cursor-pointer"
        >
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckSquare className="w-3.5 h-3.5" />}
          <span>Create Task</span>
        </button>

        <button
          type="button"
          onClick={handleReminderClick}
          disabled={loading}
          className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition-all disabled:opacity-50 cursor-pointer"
        >
          <Bell className="w-3.5 h-3.5 text-amber-400" />
          <span>Remind Me</span>
        </button>

        <button
          type="button"
          onClick={() => onDismiss(suggestion.id)}
          disabled={loading}
          className="px-3 py-2 rounded-xl bg-transparent hover:bg-slate-800 text-slate-400 hover:text-slate-200 text-xs transition-all cursor-pointer"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
};
