import React, { useState, useEffect } from 'react';
import {
  Bot,
  X,
  Edit2,
  Pause,
  Play,
  Archive,
  Layers,
  Zap,
  Activity,
  User,
  Calendar,
  Clock,
  Code,
  Plus,
  Trash2,
  Loader2
} from 'lucide-react';
import { CognitiveAgent, CognitiveAgentTriggerRecord, CognitiveAgentOutputRecord } from '../../../types/cognitive-agent';
import { useAuthStore } from '../../auth/auth-store';
import * as api from '../api/cognitive-agent-api';
import { AddTriggerModal } from './AddTriggerModal';
import { OutputDetailModal } from './OutputDetailModal';

interface CognitiveAgentDetailsModalProps {
  isOpen: boolean;
  agent: CognitiveAgent | null;
  onClose: () => void;
  onEdit: (agent: CognitiveAgent) => void;
  onToggleStatus: (agent: CognitiveAgent) => Promise<void>;
  onArchive: (agent: CognitiveAgent) => void;
  onExecute?: (agent: CognitiveAgent) => Promise<void>;
}

export const CognitiveAgentDetailsModal: React.FC<CognitiveAgentDetailsModalProps> = ({
  isOpen,
  agent,
  onClose,
  onEdit,
  onToggleStatus,
  onArchive,
  onExecute
}) => {
  const { token, currentOrg } = useAuthStore();
  const [toggling, setToggling] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [triggers, setTriggers] = useState<CognitiveAgentTriggerRecord[]>([]);
  const [outputs, setOutputs] = useState<CognitiveAgentOutputRecord[]>([]);
  const [selectedOutput, setSelectedOutput] = useState<CognitiveAgentOutputRecord | null>(null);
  const [loadingTriggers, setLoadingTriggers] = useState(false);
  const [loadingOutputs, setLoadingOutputs] = useState(false);
  const [isAddTriggerOpen, setIsAddTriggerOpen] = useState(false);

  useEffect(() => {
    if (isOpen && agent && token && currentOrg?.id) {
      setLoadingTriggers(true);
      api.fetchAgentTriggers(token, currentOrg.id, agent.id)
        .then(setTriggers)
        .catch(() => setTriggers([]))
        .finally(() => setLoadingTriggers(false));

      setLoadingOutputs(true);
      api.fetchAgentOutputs(token, currentOrg.id, agent.id)
        .then(setOutputs)
        .catch(() => setOutputs([]))
        .finally(() => setLoadingOutputs(false));
    }
  }, [isOpen, agent?.id, token, currentOrg?.id]);

  if (!isOpen || !agent) return null;

  const loadTriggers = async () => {
    if (!token || !currentOrg?.id || !agent) return;
    const data = await api.fetchAgentTriggers(token, currentOrg.id, agent.id);
    setTriggers(data);
  };

  const handlePauseTrigger = async (triggerId: string) => {
    if (!token || !currentOrg?.id || !agent) return;
    await api.pauseAgentTrigger(token, currentOrg.id, agent.id, triggerId);
    await loadTriggers();
  };

  const handleResumeTrigger = async (triggerId: string) => {
    if (!token || !currentOrg?.id || !agent) return;
    await api.resumeAgentTrigger(token, currentOrg.id, agent.id, triggerId);
    await loadTriggers();
  };

  const handleDeleteTrigger = async (triggerId: string) => {
    if (!token || !currentOrg?.id || !agent) return;
    await api.deleteAgentTrigger(token, currentOrg.id, agent.id, triggerId);
    await loadTriggers();
  };

  const handleAddTriggerSubmit = async (payload: any) => {
    if (!token || !currentOrg?.id || !agent) return;
    await api.createAgentTrigger(token, currentOrg.id, agent.id, payload);
    await loadTriggers();
  };

  const handleExecute = async () => {
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
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">ACTIVE</span>;
      case 'PAUSED':
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full">PAUSED</span>;
      case 'DISABLED':
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20 rounded-full">DISABLED</span>;
      case 'ARCHIVED':
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20 rounded-full">ARCHIVED</span>;
      default:
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-bgInput text-textMuted border border-borderColor rounded-full">{status}</span>;
    }
  };

  const handleToggle = async () => {
    setToggling(true);
    try {
      await onToggleStatus(agent);
    } finally {
      setToggling(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in">
      <div className="w-full max-w-2xl bg-bgDialog border border-borderColor p-6 rounded-2xl shadow-2xl font-outfit text-textPrimary space-y-5 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-borderMuted pb-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-2xl bg-accentSubtle text-accent flex items-center justify-center border border-accent/20 shrink-0">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold tracking-tight">{agent.name}</h2>
                {getStatusBadge(agent.status)}
              </div>
              <p className="text-xs text-textSecondary mt-0.5">{agent.description || 'No description provided.'}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-textMuted hover:text-textPrimary p-1.5 rounded-lg hover:bg-bgHover transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-bgInput p-3 rounded-xl border border-borderMuted">
          <div className="flex items-center gap-2 text-xs text-textSecondary">
            <span className="text-textMuted">Type:</span>
            <span className="font-semibold text-accentText bg-accentSubtle px-2 py-0.5 rounded-md text-[11px] border border-accent/20">
              {agent.agent_type}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {agent.status === 'ACTIVE' && onExecute && (
              <button
                onClick={handleExecute}
                disabled={executing}
                className="px-3.5 py-1.5 text-xs font-semibold text-white bg-accent hover:bg-accent/90 rounded-xl transition-all flex items-center gap-1.5 shadow-sm disabled:opacity-50"
              >
                {executing ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Executing Analysis...
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    Run Agent
                  </>
                )}
              </button>
            )}

            <button
              onClick={() => onEdit(agent)}
              className="px-3 py-1.5 text-xs font-medium text-textPrimary bg-bgCard hover:bg-bgHover border border-borderColor rounded-xl transition-all flex items-center gap-1.5"
            >
              <Edit2 className="w-3.5 h-3.5" />
              Edit
            </button>

            <button
              onClick={handleToggle}
              disabled={toggling}
              className="px-3 py-1.5 text-xs font-medium text-textPrimary bg-bgCard hover:bg-bgHover border border-borderColor rounded-xl transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              {agent.status === 'ACTIVE' ? (
                <>
                  <Pause className="w-3.5 h-3.5 text-amber-400" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 text-emerald-400" />
                  Resume
                </>
              )}
            </button>

            <button
              onClick={() => onArchive(agent)}
              className="px-3 py-1.5 text-xs font-medium text-red-400 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-xl transition-all flex items-center gap-1.5"
            >
              <Archive className="w-3.5 h-3.5" />
              Archive
            </button>
          </div>
        </div>

        {/* Overview Metadata */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 bg-bgInput rounded-xl border border-borderMuted">
            <div className="flex items-center gap-1.5 text-textMuted mb-1">
              <User className="w-3.5 h-3.5" />
              <span className="text-[10px] uppercase font-semibold">Owner</span>
            </div>
            <p className="font-medium text-textPrimary truncate">{agent.owner_user_id.substring(0, 8)}...</p>
          </div>

          <div className="p-3 bg-bgInput rounded-xl border border-borderMuted">
            <div className="flex items-center gap-1.5 text-textMuted mb-1">
              <Calendar className="w-3.5 h-3.5" />
              <span className="text-[10px] uppercase font-semibold">Created</span>
            </div>
            <p className="font-medium text-textPrimary">
              {new Date(agent.created_at).toLocaleDateString()}
            </p>
          </div>

          <div className="p-3 bg-bgInput rounded-xl border border-borderMuted">
            <div className="flex items-center gap-1.5 text-textMuted mb-1">
              <Clock className="w-3.5 h-3.5" />
              <span className="text-[10px] uppercase font-semibold">Updated</span>
            </div>
            <p className="font-medium text-textPrimary">
              {new Date(agent.updated_at).toLocaleDateString()}
            </p>
          </div>

          <div className="p-3 bg-bgInput rounded-xl border border-borderMuted">
            <div className="flex items-center gap-1.5 text-textMuted mb-1">
              <Activity className="w-3.5 h-3.5" />
              <span className="text-[10px] uppercase font-semibold">Execution</span>
            </div>
            <p className="font-medium text-textMuted">Not run yet</p>
          </div>
        </div>

        {/* System Instructions */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Code className="w-4 h-4 text-accent" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-textSecondary">System Instructions</h4>
          </div>
          <div className="p-4 bg-bgInput rounded-xl border border-borderMuted text-xs font-mono leading-relaxed text-textSecondary whitespace-pre-wrap">
            {agent.instructions}
          </div>
        </div>

        {/* Scope & Triggers & Execution Status Placeholders */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Knowledge Scope */}
          <div className="p-3.5 bg-bgInput/50 rounded-xl border border-borderMuted space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-textMuted">
                <Layers className="w-3.5 h-3.5 text-accent" />
                <h5 className="text-[11px] font-bold uppercase tracking-wider text-textSecondary">Knowledge Scope</h5>
              </div>
              <span className="px-2 py-0.5 text-[9px] font-mono font-bold bg-accentSubtle text-accent border border-accent/20 rounded-full">
                {agent.knowledge_scope?.scope_type || 'NONE'}
              </span>
            </div>
            <div className="text-xs text-textSecondary space-y-1 pt-1">
              {(!agent.knowledge_scope || (agent.knowledge_scope.scope_type as string) === 'NONE') && (
                <p className="text-textMuted text-[11px] italic">No knowledge scope configured. Agent has 0 access.</p>
              )}
              {agent.knowledge_scope?.scope_type === 'WORKSPACE' && (
                <p className="text-[11px]">Bound to entire workspace authorized knowledge.</p>
              )}
              {agent.knowledge_scope?.scope_type === 'PROJECT' && (
                <p className="text-[11px]">Scoped to Project ID: {agent.knowledge_scope.project_id || 'None'}</p>
              )}
              {agent.knowledge_scope?.scope_type === 'DOCUMENT' && (
                <p className="text-[11px]">Scoped to {agent.knowledge_scope.document_ids?.length || 0} specific document(s).</p>
              )}
              {agent.knowledge_scope?.scope_type === 'CONVERSATION' && (
                <p className="text-[11px]">Scoped to {agent.knowledge_scope.conversation_ids?.length || 0} specific conversation(s).</p>
              )}
              {agent.knowledge_scope?.scope_type === 'SELECTED_KNOWLEDGE' && (
                <p className="text-[11px]">
                  Custom union: {agent.knowledge_scope.project_id ? '1 Proj, ' : ''}
                  {agent.knowledge_scope.document_ids?.length || 0} Docs, {agent.knowledge_scope.conversation_ids?.length || 0} Convs.
                </p>
              )}
            </div>
          </div>

          {/* Triggers */}
          <div className="p-3.5 bg-bgInput/50 rounded-xl border border-borderMuted space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-textMuted">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <h5 className="text-[11px] font-bold uppercase tracking-wider text-textSecondary">Triggers & Schedules</h5>
              </div>
              <button
                onClick={() => setIsAddTriggerOpen(true)}
                className="px-2.5 py-1 text-[11px] font-semibold text-accent border border-accent/30 bg-accentSubtle hover:bg-accent/20 rounded-lg transition-all flex items-center gap-1"
              >
                <Plus className="w-3 h-3" />
                Add Trigger
              </button>
            </div>

            {loadingTriggers ? (
              <div className="py-4 text-center text-textMuted text-xs flex items-center justify-center gap-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-accent" />
                Loading agent triggers...
              </div>
            ) : triggers.length === 0 ? (
              <p className="text-xs text-textMuted italic pt-1">No automatic triggers configured. Agent runs on manual trigger.</p>
            ) : (
              <div className="space-y-2 pt-1">
                {triggers.map(t => (
                  <div key={t.id} className="p-2.5 bg-bgCard border border-borderMuted rounded-xl flex items-center justify-between text-xs">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 text-[9px] font-bold rounded-md uppercase tracking-wider ${
                          t.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                          t.status === 'PAUSED' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                          t.status === 'COMPLETED' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                          'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                        }`}>
                          {t.status}
                        </span>
                        <span className="font-semibold text-textPrimary">
                          {t.trigger_type === 'SCHEDULE' ? `${t.schedule_type} ${t.time_str || ''}` : `EVENT: ${t.event_type}`}
                        </span>
                      </div>
                      <div className="text-[11px] text-textMuted flex items-center gap-3 pt-0.5">
                        <span>Timezone: <strong className="text-textSecondary">{t.timezone}</strong></span>
                        {t.next_run_at && (
                          <span>Next run: <strong className="text-accentText">{new Date(t.next_run_at).toLocaleString()}</strong></span>
                        )}
                        {t.last_run_at && (
                          <span>Last run: <strong className="text-textSecondary">{new Date(t.last_run_at).toLocaleString()}</strong></span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                      {t.status === 'ACTIVE' ? (
                        <button
                          onClick={() => handlePauseTrigger(t.id)}
                          title="Pause Trigger"
                          className="p-1 text-amber-400 hover:text-amber-300 bg-amber-500/10 rounded-lg transition-all"
                        >
                          <Pause className="w-3.5 h-3.5" />
                        </button>
                      ) : t.status === 'PAUSED' ? (
                        <button
                          onClick={() => handleResumeTrigger(t.id)}
                          title="Resume Trigger"
                          className="p-1 text-emerald-400 hover:text-emerald-300 bg-emerald-500/10 rounded-lg transition-all"
                        >
                          <Play className="w-3.5 h-3.5" />
                        </button>
                      ) : null}

                      <button
                        onClick={() => handleDeleteTrigger(t.id)}
                        title="Delete Trigger"
                        className="p-1 text-red-400 hover:text-red-300 bg-red-500/10 rounded-lg transition-all"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Persistent Agent Outputs */}
          <div className="p-3.5 bg-bgInput/50 rounded-xl border border-borderMuted space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-textMuted">
                <Activity className="w-3.5 h-3.5 text-accent" />
                <h5 className="text-[11px] font-bold uppercase tracking-wider text-textSecondary">Persistent Agent Outputs ({outputs.length})</h5>
              </div>
            </div>

            {loadingOutputs ? (
              <div className="py-4 text-center text-textMuted text-xs flex items-center justify-center gap-2">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-accent" />
                Loading agent outputs...
              </div>
            ) : outputs.length === 0 ? (
              <p className="text-xs text-textMuted italic pt-1">No execution outputs generated yet.</p>
            ) : (
              <div className="space-y-2 pt-1">
                {outputs.map(out => (
                  <div key={out.id} className="p-3 bg-bgCard border border-borderMuted rounded-xl space-y-2 text-xs hover:border-borderColor transition-all">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 text-[9px] font-bold uppercase rounded-md bg-accentSubtle text-accent border border-accent/20">
                          {out.output_type}
                        </span>
                        <h6 className="font-semibold text-textPrimary text-xs">{out.title}</h6>
                      </div>
                      <span className="text-[10px] text-textMuted">{new Date(out.created_at).toLocaleDateString()}</span>
                    </div>

                    <p className="text-textMuted text-xs line-clamp-2 leading-relaxed">
                      {out.body}
                    </p>

                    <div className="flex items-center justify-between pt-1 border-t border-borderMuted text-[11px] text-textMuted">
                      <span>Sources: <strong className="text-textSecondary">{out.provenance?.length || 0}</strong></span>
                      <button
                        onClick={() => setSelectedOutput(out)}
                        className="px-2.5 py-1 text-[11px] font-semibold text-accent border border-accent/30 bg-accentSubtle hover:bg-accent/20 rounded-lg transition-all"
                      >
                        View Analysis
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-2 border-t border-borderMuted">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-textSecondary hover:text-textPrimary bg-bgInput hover:bg-bgHover border border-borderColor rounded-xl transition-all"
          >
            Close
          </button>
        </div>

        <AddTriggerModal
          isOpen={isAddTriggerOpen}
          onClose={() => setIsAddTriggerOpen(false)}
          onSubmit={handleAddTriggerSubmit}
        />

        <OutputDetailModal
          isOpen={!!selectedOutput}
          output={selectedOutput}
          agentName={agent.name}
          onClose={() => setSelectedOutput(null)}
        />
      </div>
    </div>
  );
};
