import React, { useState, useEffect } from 'react';
import { Edit2, X, Loader2, Info } from 'lucide-react';
import { CognitiveAgent, CognitiveAgentType, CognitiveAgentStatus, CognitiveAgentUpdate, CognitiveAgentScope } from '../../../types/cognitive-agent';
import { KnowledgeScopeSelector } from './KnowledgeScopeSelector';

interface EditAgentModalProps {
  isOpen: boolean;
  agent: CognitiveAgent | null;
  onClose: () => void;
  onSubmit: (agentId: string, data: CognitiveAgentUpdate) => Promise<void>;
}

const AGENT_TYPES: { label: string; value: CognitiveAgentType }[] = [
  { label: 'Knowledge Synthesizer', value: 'KNOWLEDGE_SYNTHESIZER' },
  { label: 'Discussion Analyzer', value: 'DISCUSSION_ANALYZER' },
  { label: 'Document Parser', value: 'DOCUMENT_PARSER' },
  { label: 'Project Monitor', value: 'PROJECT_MONITOR' },
  { label: 'Custom Agent', value: 'CUSTOM' },
];

export const EditAgentModal: React.FC<EditAgentModalProps> = ({
  isOpen,
  agent,
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
    scope_type: 'WORKSPACE'
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (agent && isOpen) {
      setName(agent.name || '');
      setDescription(agent.description || '');
      setAgentType(agent.agent_type || 'KNOWLEDGE_SYNTHESIZER');
      setInstructions(agent.instructions || '');
      setStatus(agent.status || 'ACTIVE');
      setKnowledgeScope(agent.knowledge_scope || { scope_type: 'WORKSPACE', workspace_id: agent.workspace_id });
      setError(null);
    }
  }, [agent, isOpen]);

  if (!isOpen || !agent) return null;

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

    setSaving(true);
    setError(null);

    try {
      await onSubmit(agent.id, {
        name: name.trim(),
        description: description.trim() || undefined,
        agent_type: agentType,
        instructions: instructions.trim(),
        status,
        knowledge_scope: knowledgeScope
      });

      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to update agent.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in">
      <div className="w-full max-w-xl bg-bgDialog border border-borderColor p-6 rounded-2xl shadow-2xl font-outfit text-textPrimary space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-borderMuted pb-3.5">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-xl bg-accentSubtle text-accent flex items-center justify-center border border-accent/20">
              <Edit2 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold tracking-tight">Edit Cognitive Agent</h3>
              <p className="text-[11px] text-textMuted">Modify agent parameters and configuration.</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={saving}
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
              workspaceId={agent.workspace_id}
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
                required
                disabled={saving}
                className="w-full px-3 py-2 text-xs bg-bgInput border border-borderColor rounded-xl text-textPrimary focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
              />
            </div>

            {/* Agent Type */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-textSecondary">Agent Type</label>
              <select
                value={agentType}
                onChange={(e) => setAgentType(e.target.value as CognitiveAgentType)}
                disabled={saving}
                className="w-full px-3 py-2 text-xs bg-bgInput border border-borderColor rounded-xl text-textPrimary focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
              >
                {AGENT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Status */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-textSecondary">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as CognitiveAgentStatus)}
                disabled={saving}
                className="w-full px-3 py-2 text-xs bg-bgInput border border-borderColor rounded-xl text-textPrimary focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
              >
                <option value="ACTIVE">ACTIVE</option>
                <option value="PAUSED">PAUSED</option>
                <option value="DISABLED">DISABLED</option>
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
              disabled={saving}
              className="w-full px-3 py-2 text-xs bg-bgInput border border-borderColor rounded-xl text-textPrimary focus:outline-none focus:border-accent transition-colors disabled:opacity-50"
            />
          </div>

          {/* Agent Instructions */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-textSecondary">
              Agent Instructions <span className="text-red-400">*</span>
            </label>
            <textarea
              rows={4}
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              required
              disabled={saving}
              className="w-full p-3 text-xs font-mono bg-bgInput border border-borderColor rounded-xl text-textPrimary focus:outline-none focus:border-accent transition-colors leading-relaxed disabled:opacity-50"
            />
          </div>
          </>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-borderMuted">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 text-xs font-medium text-textSecondary hover:text-textPrimary bg-bgInput hover:bg-bgHover border border-borderColor rounded-xl transition-all disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 text-xs font-semibold text-white bg-accent hover:bg-accent/90 rounded-xl shadow-sm transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              {saving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Saving Changes...
                </>
              ) : (
                'Save Changes'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
