import React, { useState } from 'react';
import {
  Bot,
  Edit2,
  Pause,
  Play,
  Archive,
  Eye,
  Calendar,
  Layers,
  Activity,
  User,
  Loader2
} from 'lucide-react';
import { CognitiveAgent } from '../../../types/cognitive-agent';

interface CognitiveAgentCardProps {
  agent: CognitiveAgent;
  onOpen: (agent: CognitiveAgent) => void;
  onEdit: (agent: CognitiveAgent) => void;
  onToggleStatus: (agent: CognitiveAgent) => Promise<void>;
  onArchive: (agent: CognitiveAgent) => void;
  onExecute?: (agent: CognitiveAgent) => Promise<void>;
}

export const CognitiveAgentCard: React.FC<CognitiveAgentCardProps> = ({
  agent,
  onOpen,
  onEdit,
  onToggleStatus,
  onArchive,
  onExecute
}) => {
  const [toggling, setToggling] = useState(false);
  const [executing, setExecuting] = useState(false);

  const handleToggle = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setToggling(true);
    try {
      await onToggleStatus(agent);
    } finally {
      setToggling(false);
    }
  };

  const handleExecute = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!onExecute) return;
    setExecuting(true);
    try {
      await onExecute(agent);
    } finally {
      setExecuting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return <span className="px-2.5 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">ACTIVE</span>;
      case 'PAUSED':
        return <span className="px-2.5 py-0.5 text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full">PAUSED</span>;
      case 'DISABLED':
        return <span className="px-2.5 py-0.5 text-[10px] font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20 rounded-full">DISABLED</span>;
      case 'ARCHIVED':
        return <span className="px-2.5 py-0.5 text-[10px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20 rounded-full">ARCHIVED</span>;
      default:
        return <span className="px-2.5 py-0.5 text-[10px] font-semibold bg-bgInput text-textMuted border border-borderColor rounded-full">{status}</span>;
    }
  };

  return (
    <div
      onClick={() => onOpen(agent)}
      className="p-4 sm:p-5 bg-bgCard border border-borderColor rounded-2xl shadow-sm hover:shadow-md hover:border-accent/30 transition-all cursor-pointer font-outfit text-textPrimary flex flex-col justify-between space-y-4 group"
    >
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-accentSubtle text-accent flex items-center justify-center border border-accent/20 shrink-0 group-hover:scale-105 transition-transform">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-bold text-sm text-textPrimary group-hover:text-accent transition-colors">
                {agent.name}
              </h4>
              <span className="text-[10px] text-accentText font-medium bg-accentSubtle/50 px-2 py-0.5 rounded-md border border-accent/10">
                {agent.agent_type}
              </span>
            </div>
          </div>
          {getStatusBadge(agent.status)}
        </div>

        {/* Description */}
        <p className="text-xs text-textSecondary leading-relaxed line-clamp-2 min-h-[2.25rem]">
          {agent.description || 'No description provided.'}
        </p>

        {/* System Prompt Instructions Snippet */}
        <div className="bg-bgInput p-2.5 rounded-xl border border-borderMuted">
          <span className="text-[9px] text-textMuted uppercase block mb-1 font-semibold tracking-wider">
            Instructions Configuration
          </span>
          <p className="text-[11px] text-textSecondary font-mono italic line-clamp-2">
            "{agent.instructions}"
          </p>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
          <div className="flex items-center gap-1.5 text-textMuted">
            <Layers className="w-3.5 h-3.5 shrink-0" />
            <span className="truncate">Scope: Workspace</span>
          </div>

          <div className="flex items-center gap-1.5 text-textMuted">
            <Activity className="w-3.5 h-3.5 shrink-0" />
            <span className="truncate">Status: Not run yet</span>
          </div>

          <div className="flex items-center gap-1.5 text-textMuted">
            <User className="w-3.5 h-3.5 shrink-0" />
            <span className="truncate">Owner: You</span>
          </div>

          <div className="flex items-center gap-1.5 text-textMuted">
            <Calendar className="w-3.5 h-3.5 shrink-0" />
            <span className="truncate">{new Date(agent.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-borderMuted" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => onOpen(agent)}
            className="px-3 py-1.5 text-xs font-medium text-textSecondary hover:text-textPrimary bg-bgInput hover:bg-bgHover border border-borderColor rounded-xl transition-all flex items-center gap-1.5"
          >
            <Eye className="w-3.5 h-3.5" />
            Open
          </button>

          {agent.status === 'ACTIVE' && onExecute && (
            <button
              onClick={handleExecute}
              disabled={executing}
              className="px-3 py-1.5 text-xs font-semibold text-white bg-accent hover:bg-accent/90 rounded-xl transition-all flex items-center gap-1.5 shadow-xs disabled:opacity-50"
            >
              {executing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  Run Agent
                </>
              )}
            </button>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => onEdit(agent)}
            title="Edit Agent"
            className="p-1.5 text-textMuted hover:text-textPrimary bg-bgInput hover:bg-bgHover border border-borderColor rounded-xl transition-all"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleToggle}
            disabled={toggling}
            title={agent.status === 'ACTIVE' ? 'Pause Agent' : 'Resume Agent'}
            className="p-1.5 text-textMuted hover:text-textPrimary bg-bgInput hover:bg-bgHover border border-borderColor rounded-xl transition-all disabled:opacity-50"
          >
            {toggling ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : agent.status === 'ACTIVE' ? (
              <Pause className="w-3.5 h-3.5 text-amber-400" />
            ) : (
              <Play className="w-3.5 h-3.5 text-emerald-400" />
            )}
          </button>

          <button
            onClick={() => onArchive(agent)}
            title="Archive Agent"
            className="p-1.5 text-red-400 hover:text-red-300 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-xl transition-all"
          >
            <Archive className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
