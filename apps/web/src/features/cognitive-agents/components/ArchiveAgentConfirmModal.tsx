import React, { useState } from 'react';
import { AlertTriangle, X, Loader2 } from 'lucide-react';
import { CognitiveAgent } from '../../../types/cognitive-agent';

interface ArchiveAgentConfirmModalProps {
  isOpen: boolean;
  agent: CognitiveAgent | null;
  onClose: () => void;
  onConfirm: (agentId: string) => Promise<void>;
}

export const ArchiveAgentConfirmModal: React.FC<ArchiveAgentConfirmModalProps> = ({
  isOpen,
  agent,
  onClose,
  onConfirm
}) => {
  const [archiving, setArchiving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !agent) return null;

  const handleConfirm = async () => {
    setArchiving(true);
    setError(null);
    try {
      await onConfirm(agent.id);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to archive agent.');
    } finally {
      setArchiving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in">
      <div className="w-full max-w-md bg-bgDialog border border-borderColor p-5 rounded-2xl shadow-2xl font-outfit text-textPrimary space-y-4">
        <div className="flex items-center justify-between border-b border-borderMuted pb-3">
          <div className="flex items-center gap-2 text-red-400">
            <AlertTriangle className="w-5 h-5" />
            <h3 className="text-sm font-bold tracking-tight">Archive Agent</h3>
          </div>
          <button
            onClick={onClose}
            disabled={archiving}
            className="text-textMuted hover:text-textPrimary p-1 rounded-lg hover:bg-bgHover transition-colors disabled:opacity-50"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-xs">
            {error}
          </div>
        )}

        <div className="text-xs text-textSecondary space-y-2 leading-relaxed">
          <p>
            Are you sure you want to archive <strong className="text-textPrimary">{agent.name}</strong>?
          </p>
          <p className="text-textMuted text-[11px]">
            Archived agents will no longer appear in the active agent list. Historical execution logs and outputs will remain preserved for audit compliance.
          </p>
        </div>

        <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-borderMuted">
          <button
            type="button"
            onClick={onClose}
            disabled={archiving}
            className="px-4 py-2 text-xs font-medium text-textSecondary hover:text-textPrimary bg-bgInput hover:bg-bgHover border border-borderColor rounded-xl transition-all disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={archiving}
            className="px-4 py-2 text-xs font-semibold text-white bg-red-600 hover:bg-red-500 rounded-xl shadow-sm transition-all flex items-center gap-1.5 disabled:opacity-50"
          >
            {archiving ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Archiving...
              </>
            ) : (
              'Archive Agent'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
