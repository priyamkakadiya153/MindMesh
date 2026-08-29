import React, { useState, useEffect, useCallback } from 'react';
import {
  Bot,
  Plus,
  Sparkles,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Cpu,
  PlayCircle,
  PauseCircle,
  Sliders
} from 'lucide-react';
import { CognitiveAgent, CognitiveAgentCreate, CognitiveAgentUpdate } from '../../../types/cognitive-agent';
import { useAuthStore } from '../../auth/auth-store';
import { useWorkspaceStore } from '../../workspace/store';
import * as api from '../api/cognitive-agent-api';
import { CognitiveAgentCard } from './CognitiveAgentCard';
import { CreateAgentModal } from './CreateAgentModal';
import { EditAgentModal } from './EditAgentModal';
import { CognitiveAgentDetailsModal } from './CognitiveAgentDetailsModal';
import { ArchiveAgentConfirmModal } from './ArchiveAgentConfirmModal';

export const CognitiveAgentsPage: React.FC = () => {
  const { token, currentOrg, loading: authLoading } = useAuthStore();
  const { currentWorkspace, loading: workspaceLoading } = useWorkspaceStore();

  const [agents, setAgents] = useState<CognitiveAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<CognitiveAgent | null>(null);
  const [inspectingAgent, setInspectingAgent] = useState<CognitiveAgent | null>(null);
  const [archivingAgent, setArchivingAgent] = useState<CognitiveAgent | null>(null);

  const showToast = (text: string, type: 'success' | 'error' = 'success') => {
    setToastMessage({ type, text });
    setTimeout(() => setToastMessage(null), 4000);
  };

  const loadAgents = useCallback(async () => {
    // If auth or workspace stores are still initializing, maintain initial page loading state
    if (authLoading || workspaceLoading) {
      return;
    }

    if (!token || !currentOrg?.id) {
      setAgents([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.fetchCognitiveAgents(
        token,
        currentOrg.id,
        currentWorkspace?.id
      );
      setAgents(data);
    } catch (err: any) {
      setError(err.message || 'Unable to load Cognitive Agents.');
    } finally {
      setLoading(false);
    }
  }, [token, currentOrg?.id, currentWorkspace?.id, authLoading, workspaceLoading]);

  useEffect(() => {
    loadAgents();
  }, [loadAgents]);

  // Statistics
  const totalAgents = agents.length;
  const activeCount = agents.filter(a => a.status === 'ACTIVE').length;
  const pausedCount = agents.filter(a => a.status === 'PAUSED').length;
  const draftCount = agents.filter(a => a.status === 'DISABLED' || a.status === 'ARCHIVED').length;

  // Handlers
  const handleCreateSubmit = async (data: CognitiveAgentCreate) => {
    if (!token || !currentOrg?.id) return;
    const created = await api.createCognitiveAgent(token, currentOrg.id, data);
    setAgents(prev => [created, ...prev]);
    showToast('Agent created successfully.');
  };

  const handleEditSubmit = async (agentId: string, data: CognitiveAgentUpdate) => {
    if (!token || !currentOrg?.id) return;
    const updated = await api.updateCognitiveAgent(token, currentOrg.id, agentId, data);
    setAgents(prev => prev.map(a => (a.id === agentId ? updated : a)));
    if (inspectingAgent?.id === agentId) {
      setInspectingAgent(updated);
    }
    showToast('Agent updated successfully.');
  };

  const handleToggleStatus = async (agent: CognitiveAgent) => {
    if (!token || !currentOrg?.id) return;
    const nextStatus = agent.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';
    try {
      const updated = await api.updateCognitiveAgent(token, currentOrg.id, agent.id, {
        status: nextStatus
      });
      setAgents(prev => prev.map(a => (a.id === agent.id ? updated : a)));
      if (inspectingAgent?.id === agent.id) {
        setInspectingAgent(updated);
      }
      showToast(`Agent ${nextStatus === 'ACTIVE' ? 'resumed' : 'paused'} successfully.`);
    } catch (err: any) {
      showToast(err.message || 'Failed to update agent status.', 'error');
    }
  };

  const handleArchiveConfirm = async (agentId: string) => {
    if (!token || !currentOrg?.id) return;
    await api.archiveCognitiveAgent(token, currentOrg.id, agentId);
    setAgents(prev => prev.filter(a => a.id !== agentId));
    if (inspectingAgent?.id === agentId) {
      setInspectingAgent(null);
    }
    showToast('Agent archived successfully.');
  };

  const handleBrowseTemplates = () => {
    showToast('Template library coming in a future update.', 'success');
  };

  const handleExecuteAgent = async (agent: CognitiveAgent) => {
    if (!token || !currentOrg?.id) return;
    try {
      const result = await api.executeCognitiveAgent(token, currentOrg.id, agent.id);
      if (result.execution.status === 'COMPLETED') {
        showToast(`Agent executed successfully! Output: "${result.output?.title || 'Analysis Result'}"`, 'success');
      } else {
        showToast(`Agent execution failed: ${result.execution.error_message || 'Unknown error'}`, 'error');
      }
      const data = await api.fetchCognitiveAgents(token, currentOrg.id, currentWorkspace?.id);
      setAgents(data);
    } catch (err: any) {
      showToast(err.message || 'Failed to execute agent', 'error');
    }
  };

  return (
    <div className="space-y-6 font-outfit text-textPrimary animate-fadeIn">
      {/* Toast Notification Banner */}
      {toastMessage && (
        <div
          className={`fixed bottom-5 right-5 z-[100] px-4 py-3 rounded-2xl shadow-xl border flex items-center gap-2.5 text-xs font-medium backdrop-blur-md transition-all animate-bounce ${
            toastMessage.type === 'success'
              ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300'
              : 'bg-red-500/15 border-red-500/30 text-red-300'
          }`}
        >
          {toastMessage.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          )}
          <span>{toastMessage.text}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-borderMuted pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="h-9 w-9 rounded-2xl bg-accentSubtle text-accent flex items-center justify-center border border-accent/20">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-textPrimary">Cognitive Agents</h1>
              <p className="text-xs text-textSecondary mt-0.5">
                Create specialized AI workers for knowledge analysis, monitoring, and intelligence.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 self-start sm:self-auto">
          <button
            onClick={handleBrowseTemplates}
            className="px-3.5 py-2 text-xs font-medium text-textSecondary hover:text-textPrimary bg-bgCard hover:bg-bgHover border border-borderColor rounded-xl transition-all flex items-center gap-1.5 shadow-xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            Browse Templates
          </button>

          <button
            onClick={() => setIsCreateOpen(true)}
            className="px-4 py-2 text-xs font-semibold text-white bg-accent hover:bg-accent/90 rounded-xl shadow-sm transition-all flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            Create Agent
          </button>
        </div>
      </div>

      {/* Summary Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <div className="p-4 bg-bgCard border border-borderColor rounded-2xl shadow-xs flex items-center justify-between min-h-[4.5rem]">
          <div>
            <span className="text-[10px] font-semibold text-textMuted uppercase tracking-wider block">
              Total Agents
            </span>
            {loading ? (
              <div className="h-6 w-10 bg-bgInput/80 rounded-lg animate-pulse my-0.5" />
            ) : (
              <span className="text-xl font-extrabold text-textPrimary mt-0.5 block">
                {totalAgents}
              </span>
            )}
          </div>
          <div className="h-9 w-9 rounded-xl bg-accentSubtle text-accent flex items-center justify-center border border-accent/20 shrink-0">
            <Cpu className="w-4.5 h-4.5" />
          </div>
        </div>

        <div className="p-4 bg-bgCard border border-borderColor rounded-2xl shadow-xs flex items-center justify-between min-h-[4.5rem]">
          <div>
            <span className="text-[10px] font-semibold text-textMuted uppercase tracking-wider block">
              Active
            </span>
            {loading ? (
              <div className="h-6 w-10 bg-emerald-500/20 rounded-lg animate-pulse my-0.5" />
            ) : (
              <span className="text-xl font-extrabold text-emerald-400 mt-0.5 block">
                {activeCount}
              </span>
            )}
          </div>
          <div className="h-9 w-9 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20 shrink-0">
            <PlayCircle className="w-4.5 h-4.5" />
          </div>
        </div>

        <div className="p-4 bg-bgCard border border-borderColor rounded-2xl shadow-xs flex items-center justify-between min-h-[4.5rem]">
          <div>
            <span className="text-[10px] font-semibold text-textMuted uppercase tracking-wider block">
              Paused
            </span>
            {loading ? (
              <div className="h-6 w-10 bg-amber-500/20 rounded-lg animate-pulse my-0.5" />
            ) : (
              <span className="text-xl font-extrabold text-amber-400 mt-0.5 block">
                {pausedCount}
              </span>
            )}
          </div>
          <div className="h-9 w-9 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center border border-amber-500/20 shrink-0">
            <PauseCircle className="w-4.5 h-4.5" />
          </div>
        </div>

        <div className="p-4 bg-bgCard border border-borderColor rounded-2xl shadow-xs flex items-center justify-between min-h-[4.5rem]">
          <div>
            <span className="text-[10px] font-semibold text-textMuted uppercase tracking-wider block">
              Draft / Other
            </span>
            {loading ? (
              <div className="h-6 w-10 bg-bgInput/80 rounded-lg animate-pulse my-0.5" />
            ) : (
              <span className="text-xl font-extrabold text-textMuted mt-0.5 block">
                {draftCount}
              </span>
            )}
          </div>
          <div className="h-9 w-9 rounded-xl bg-bgInput text-textMuted flex items-center justify-center border border-borderColor shrink-0">
            <Sliders className="w-4.5 h-4.5" />
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        /* Loading Skeletons */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-1">
          {[1, 2, 3].map(i => (
            <div
              key={i}
              className="p-4 sm:p-5 bg-bgCard border border-borderColor rounded-2xl shadow-xs space-y-4 animate-pulse flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 bg-bgInput rounded-xl shrink-0" />
                    <div className="space-y-1.5 flex-1">
                      <div className="h-4 bg-bgInput rounded w-28" />
                      <div className="h-3 bg-bgInput/60 rounded w-16" />
                    </div>
                  </div>
                  <div className="h-5 w-14 bg-bgInput rounded-full" />
                </div>
                <div className="h-9 bg-bgInput/50 rounded-xl w-full" />
              </div>
              <div className="pt-2 border-t border-borderColor/60 flex items-center justify-between">
                <div className="h-3 bg-bgInput/40 rounded w-20" />
                <div className="flex items-center gap-1.5">
                  <div className="h-7 w-7 bg-bgInput rounded-lg" />
                  <div className="h-7 w-7 bg-bgInput rounded-lg" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        /* Error State */
        <div className="p-8 bg-red-500/10 border border-red-500/20 rounded-2xl text-center space-y-3">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto" />
          <div>
            <h3 className="text-sm font-bold text-red-300">Unable to load Cognitive Agents</h3>
            <p className="text-xs text-red-400/80 mt-1 max-w-md mx-auto">{error}</p>
          </div>
          <button
            onClick={loadAgents}
            className="px-4 py-2 text-xs font-semibold text-white bg-red-600 hover:bg-red-500 rounded-xl shadow-xs transition-all inline-flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry
          </button>
        </div>
      ) : agents.length === 0 ? (
        /* Empty State */
        <div className="p-10 text-center bg-bgCard border border-borderColor rounded-2xl space-y-4 font-outfit max-w-xl mx-auto my-6">
          <div className="h-12 w-12 rounded-2xl bg-accentSubtle text-accent mx-auto flex items-center justify-center border border-accent/20">
            <Bot className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-textPrimary">No Cognitive Agents yet</h3>
            <p className="text-xs text-textSecondary max-w-sm mx-auto leading-relaxed">
              Create a specialized AI worker to analyze your workspace knowledge, parse discussions, or monitor project tasks.
            </p>
          </div>
          <button
            onClick={() => setIsCreateOpen(true)}
            className="px-4 py-2 text-xs font-semibold text-white bg-accent hover:bg-accent/90 rounded-xl shadow-sm transition-all inline-flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" />
            Create Agent
          </button>
        </div>
      ) : (
        /* Agent Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-1">
          {agents.map(agent => (
            <CognitiveAgentCard
              key={agent.id}
              agent={agent}
              onOpen={setInspectingAgent}
              onEdit={setEditingAgent}
              onToggleStatus={handleToggleStatus}
              onArchive={setArchivingAgent}
              onExecute={handleExecuteAgent}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      <CreateAgentModal
        isOpen={isCreateOpen}
        workspaceId={currentWorkspace?.id}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={handleCreateSubmit}
      />

      <EditAgentModal
        isOpen={!!editingAgent}
        agent={editingAgent}
        onClose={() => setEditingAgent(null)}
        onSubmit={handleEditSubmit}
      />

      <CognitiveAgentDetailsModal
        isOpen={!!inspectingAgent}
        agent={inspectingAgent}
        onClose={() => setInspectingAgent(null)}
        onEdit={agent => {
          setInspectingAgent(null);
          setEditingAgent(agent);
        }}
        onToggleStatus={handleToggleStatus}
        onArchive={agent => {
          setInspectingAgent(null);
          setArchivingAgent(agent);
        }}
        onExecute={handleExecuteAgent}
      />

      <ArchiveAgentConfirmModal
        isOpen={!!archivingAgent}
        agent={archivingAgent}
        onClose={() => setArchivingAgent(null)}
        onConfirm={handleArchiveConfirm}
      />
    </div>
  );
};
