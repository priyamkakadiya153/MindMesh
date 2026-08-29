import React, { useState } from 'react';
import { ActionRecommendation, executeAction } from '../actions-api';
import { Sparkles, CheckCircle2, AlertTriangle, ArrowRight, Loader2, FileText, CheckSquare, X } from 'lucide-react';

interface ActionableCardProps {
  action: ActionRecommendation;
  token?: string;
  workspaceId?: string;
  onExecuted?: (result: any) => void;
  onDismiss?: (actionId: string) => void;
}

export const ActionableCard: React.FC<ActionableCardProps> = ({
  action,
  token,
  workspaceId,
  onExecuted,
  onDismiss
}) => {
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [editedPayload, setEditedPayload] = useState<Record<string, any>>(action.payload || {});
  const [resultMessage, setResultMessage] = useState<string | null>(null);

  const handleConfirm = async () => {
    setIsExecuting(true);
    try {
      const res = await executeAction(action.action_type, editedPayload, workspaceId, token);
      setResultMessage(res.message);
      if (onExecuted) onExecuted(res);
      setTimeout(() => {
        setIsModalOpen(false);
      }, 1200);
    } catch (err) {
      console.error('Failed to execute action:', err);
      setResultMessage('Action execution failed. Please retry.');
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <>
      {/* Action Card */}
      <div className="bg-slate-900/70 border border-slate-800 p-4 rounded-3xl space-y-3 font-sans text-xs hover:border-slate-700 transition-all shadow-md">
        <div className="flex items-center justify-between">
          <span className="text-[9px] font-mono font-bold uppercase text-indigo-400 px-2 py-0.5 bg-indigo-950/80 rounded border border-indigo-800/60 flex items-center space-x-1">
            <Sparkles className="w-3 h-3 text-indigo-400" />
            <span>SUGGESTED ACTION</span>
          </span>

          <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
            action.priority === 'HIGH'
              ? 'bg-rose-950/60 text-rose-400 border-rose-800/60'
              : 'bg-slate-800 text-slate-300 border-slate-700'
          }`}>
            {action.priority} PRIORITY
          </span>
        </div>

        <div>
          <h4 className="font-bold text-slate-100 text-sm">{action.title}</h4>
          <p className="text-[11px] text-slate-400 mt-1 italic bg-slate-950 p-2.5 rounded-xl border border-slate-800">
            Why: "{action.why}"
          </p>
        </div>

        <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
          <span>Result: {action.expected_result}</span>

          <div className="flex items-center space-x-2">
            {onDismiss && (
              <button
                type="button"
                onClick={() => onDismiss(action.id)}
                className="px-2.5 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 font-semibold"
              >
                Dismiss
              </button>
            )}

            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold shadow-md transition-all flex items-center space-x-1"
            >
              <span>Review Action</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Confirmation & Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-3xl p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                <h3 className="text-sm font-bold text-white">Confirm Action Execution</h3>
              </div>

              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Action Title / Payload</label>
                <input
                  type="text"
                  value={editedPayload.title || action.title}
                  onChange={(e) => setEditedPayload({ ...editedPayload, title: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 px-3 py-2 rounded-xl text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800 text-[11px] text-slate-400 space-y-1">
                <span className="block font-bold text-slate-300">Evidence Source: {action.source_type}</span>
                <span>MindMesh will record this action on the timeline and update knowledge graph connections.</span>
              </div>

              {resultMessage && (
                <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 rounded-xl text-center font-bold flex items-center justify-center space-x-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{resultMessage}</span>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={handleConfirm}
                disabled={isExecuting}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md transition-all flex items-center space-x-1.5"
              >
                {isExecuting ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                <span>Confirm & Execute</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
