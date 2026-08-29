import React, { useState } from 'react';
import { ActionProposalData, ActionResultData, confirmActionProposal } from '../chat-api';
import { useAuth } from '../../auth/auth-provider';
import { CheckCircle2, XCircle, Loader2, Sparkles, AlertCircle, Layers } from 'lucide-react';

interface ActionProposalCardProps {
  proposal: ActionProposalData;
  onActionResult?: (result: ActionResultData) => void;
}

export const ActionProposalCard: React.FC<ActionProposalCardProps> = ({
  proposal,
  onActionResult
}) => {
  const { token } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ActionResultData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAction = async (confirm: boolean) => {
    if (submitting || result) return;
    setSubmitting(true);
    setError(null);

    try {
      const res = await confirmActionProposal(token || '', {
        proposal_id: proposal.proposal_id,
        intent_type: proposal.intent_type,
        parameters: proposal.parameters || {},
        confirm
      });
      setResult(res);
      if (onActionResult) onActionResult(res);
    } catch (err: any) {
      console.error('Failed to confirm action proposal:', err);
      setError(err?.response?.data?.message || 'Failed to process action request.');
    } finally {
      setSubmitting(false);
    }
  };

  const isConfirmed = result?.status === 'SUCCESS';
  const isCancelled = result?.status === 'CANCELLED';
  const isNotImplemented = result?.status === 'NOT_IMPLEMENTED';

  const intentLabel = (proposal?.intent_type || 'CREATE_TASK').toString().replace(/_/g, ' ');
  const taskTitle = proposal?.parameters?.title || proposal?.parameters?.raw_query;
  const dueDate = proposal?.parameters?.due_date_str || proposal?.parameters?.due_date;
  const assigneeName = proposal?.parameters?.assignee_name || proposal?.parameters?.assignee;
  const recipientName = proposal?.parameters?.recipient_name || proposal?.parameters?.recipient;

  return (
    <div className="my-3 p-4 rounded-2xl bg-bgSidebar border border-indigo-500/30 shadow-md space-y-3 max-w-md">
      {/* Header Badge */}
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center gap-1">
          <Sparkles className="w-3 h-3" />
          <span>Action Proposal ({intentLabel})</span>
        </span>
        {result && (
          <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
            isConfirmed ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
            isCancelled ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
            'bg-slate-500/10 text-slate-300 border border-slate-500/20'
          }`}>
            {result.status}
          </span>
        )}
      </div>

      {/* Main Title & Parameters */}
      <div className="space-y-1">
        <h4 className="text-sm font-bold text-textPrimary leading-snug">{proposal.title}</h4>
        {proposal.description && (
          <p className="text-xs text-textMuted">{proposal.description}</p>
        )}
      </div>

      {/* Parameters Summary */}
      {proposal.parameters && Object.keys(proposal.parameters).length > 0 && (
        <div className="p-3 rounded-xl bg-bgCard border border-borderColor/60 space-y-1 text-xs text-textPrimary">
          {taskTitle && (
            <div><span className="text-textMuted">Task Title:</span> <strong>{taskTitle}</strong></div>
          )}
          {assigneeName && (
            <div><span className="text-textMuted">Assignee:</span> <strong>{assigneeName}</strong></div>
          )}
          {dueDate && (
            <div><span className="text-textMuted">Due:</span> <strong>{dueDate}</strong></div>
          )}
          {recipientName && (
            <div><span className="text-textMuted">Recipient:</span> <strong>{recipientName}</strong></div>
          )}
        </div>
      )}

      {/* Execution Result Message */}
      {result && (
        <div className={`p-3 rounded-xl border text-xs leading-relaxed ${
          isConfirmed ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' :
          isCancelled ? 'bg-amber-500/10 border-amber-500/30 text-amber-300' :
          'bg-slate-500/10 border-slate-500/30 text-slate-300'
        }`}>
          {result.message}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
          {error}
        </div>
      )}

      {/* Action Buttons (Confirm / Cancel) */}
      {!result && (
        <div className="flex items-center gap-2 pt-1">
          <button
            onClick={() => handleAction(true)}
            disabled={submitting}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-sm transition-all disabled:opacity-50"
          >
            {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
            <span>Confirm & Execute</span>
          </button>

          <button
            onClick={() => handleAction(false)}
            disabled={submitting}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 px-4 rounded-xl bg-bgHover hover:bg-borderColor text-textMuted hover:text-textPrimary font-bold text-xs transition-all disabled:opacity-50"
          >
            <XCircle className="w-3.5 h-3.5" />
            <span>Cancel</span>
          </button>
        </div>
      )}
    </div>
  );
};
