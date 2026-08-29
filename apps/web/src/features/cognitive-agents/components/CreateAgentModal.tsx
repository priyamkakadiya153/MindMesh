import React, { useState } from 'react';
import { Bot, X, Loader2, Info } from 'lucide-react';
import { CognitiveAgentType, CognitiveAgentStatus, CognitiveAgentCreate, CognitiveAgentScope } from '../../../types/cognitive-agent';
import { KnowledgeScopeSelector } from './KnowledgeScopeSelector';

interface CreateAgentModalProps {
  isOpen: boolean;
  workspaceId?: string;
  onClose: () => void;
  onSubmit: (data: CognitiveAgentCreate) => Promise<void>;
}

const AGENT_TYPES: { label: string; value: CognitiveAgentType; desc: string }[] = [
  { label: 'Knowledge Synthesizer', value: 'KNOWLEDGE_SYNTHESIZER', desc: 'Synthesizes insights across workspace conversations and files.' },
  { label: 'Discussion Analyzer', value: 'DISCUSSION_ANALYZER', desc: 'Parses chat threads to extract decisions, blocker alerts, and summaries.' },
  { label: 'Document Parser', value: 'DOCUMENT_PARSER', desc: 'Analyzes document structures, extracts metadata, and indexes knowledge.' },
  { label: 'Project Monitor', value: 'PROJECT_MONITOR', desc: 'Tracks project tasks, deadlines, and operational follow-ups.' },
  { label: 'Custom Agent', value: 'CUSTOM', desc: 'Specialized domain worker tailored for custom workspace instructions.' },
];

export const CreateAgentModal: React.FC<CreateAgentModalProps> = ({
  isOpen,
  workspaceId,
  onClose,
  onSubmit
}) => {
  const [activeTab, setActiveTab] = useState<'config' | 'scope'>('config');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [agentType, setAgentType] = useState<CognitiveAgentType>('KNOWLEDGE_SYNTHESIZER');
  const [instructions, setInstructions] = useState('');
  const [status, setStatus] = useState<CognitiveAgentStatus>('ACTIVE');
  const [knowledgeScope, setKnowledgeScope] = useState<CognitiveAgentScope>({
    scope_type: 'WORKSPACE',
    workspace_id: workspaceId
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Agent name is required.');
      return;
    }
    if (!instructions.trim()) {
      setError('Agent instructions are required.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await onSubmit({
        name: name.trim(),
        description: description.trim() || undefined,
        agent_type: agentType,
        instructions: instructions.trim(),
        status,
        workspace_id: workspaceId,
        knowledge_scope: knowledgeScope
      });

      // Reset form
      setName('');
      setDescription('');
      setAgentType('KNOWLEDGE_SYNTHESIZER');
      setInstructions('');
      setStatus('ACTIVE');
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create agent.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in">
      <div className="w-full max-w-xl bg-bgDialog border border-borderColor p-6 rounded-2xl shadow-2xl font-outfit text-textPrimary space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-borderMuted pb-3.5">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-xl bg-accentSubtle text-accent flex items-center justify-center border border-accent/20">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold tracking-tight">Create Cognitive Agent</h3>
              <p className="text-[11px] text-textMuted">Configure a new specialized AI worker for your workspace.</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={submitting}
            className="text-textMuted hover:text-textPrimary p-1 rounded-lg hover:bg-bgHover transition-colors disabled:opacity-50"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-borderMuted text-xs font-semibold gap-4">
          <button
            type="button"
            onClick={() => setActiveTab('config')}
            className={`pb-2 transition-colors border-b-2 ${
              activeTab === 'config'
                ? 'border-accent text-accent'
                : 'border-transparent text-textMuted hover:text-textPrimary'
            }`}
          >
            Agent Parameters
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('scope')}
            className={`pb-2 transition-colors border-b-2 ${
              activeTab === 'scope'
                ? 'border-accent text-accent'
                : 'border-transparent text-textMuted hover:text-textPrimary'
            }`}
          >
            Knowledge Access
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-xs flex items-center gap-2">
            <Info className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {activeTab === 'scope' ? (
            <KnowledgeScopeSelector
              workspaceId={workspaceId}
              scope={knowledgeScope}
              onChange={setKnowledgeScope}
            />
          ) : (
            <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Agent Name */}
            <div className="space-y-1.5 sm:col-span-2">
              <label className="text-xs font-semibold text-textSecondary">
                Agent Name <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Project Monitor"
                required
                disabled={submitting}
                className="w-full px-3 py-2 text-xs bg-bgInput border border-borderColor rounded-xl text-textPrimary placeholder:text-textMuted focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
              />
            </div>

            {/* Agent Type */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-textSecondary">Agent Type</label>
              <select
                value={agentType}
                onChange={(e) => setAgentType(e.target.value as CognitiveAgentType)}
                disabled={submitting}
                className="w-full px-3 py-2 text-xs bg-bgInput border border-borderColor rounded-xl text-textPrimary focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
              >
                {AGENT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Initial Status */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-textSecondary">Initial Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as CognitiveAgentStatus)}
                disabled={submitting}
                className="w-full px-3 py-2 text-xs bg-bgInput border border-borderColor rounded-xl text-textPrimary focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
              >
                <option value="ACTIVE">ACTIVE — Enabled for workspace</option>
                <option value="PAUSED">PAUSED — Configuration only</option>
              </select>
            </div>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-textSecondary">Description</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Monitors project conversations for deadlines, blockers, and follow-ups."
              disabled={submitting}
              className="w-full px-3 py-2 text-xs bg-bgInput border border-borderColor rounded-xl text-textPrimary placeholder:text-textMuted focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
            />
          </div>

          {/* Agent Instructions */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-textSecondary">
                Agent Instructions <span className="text-red-400">*</span>
              </label>
              <span className="text-[10px] text-textMuted">System Configuration</span>
            </div>
            <textarea
              rows={4}
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="Describe what this agent should analyze and what kind of intelligence it should produce..."
              required
              disabled={submitting}
              className="w-full p-3 text-xs font-mono bg-bgInput border border-borderColor rounded-xl text-textPrimary placeholder:text-textMuted focus:outline-none focus:border-accent transition-colors leading-relaxed disabled:opacity-50"
            />
            <p className="text-[10px] text-textMuted leading-normal">
              Instructions define the agent's specialization and reasoning constraints. Creating an agent saves configuration only and does not execute queries or LLM tasks.
            </p>
          </div>
          </>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-borderMuted">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 text-xs font-medium text-textSecondary hover:text-textPrimary bg-bgInput hover:bg-bgHover border border-borderColor rounded-xl transition-all disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 text-xs font-semibold text-white bg-accent hover:bg-accent/90 rounded-xl shadow-sm transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Creating Agent...
                </>
              ) : (
                'Create Agent'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
