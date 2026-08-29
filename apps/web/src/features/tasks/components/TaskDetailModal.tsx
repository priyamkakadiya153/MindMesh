import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TaskItem, TaskProvenance, fetchTaskWhyProvenance, completeTask } from '../task-api';
import {
  X, CheckCircle2, HelpCircle, Sparkles, Clock, User, Briefcase,
  ArrowUpRight, AlertTriangle, Layers, ShieldCheck, FileText, MessageSquare
} from 'lucide-react';

interface TaskDetailModalProps {
  task: TaskItem | null;
  token?: string;
  onClose: () => void;
  onTaskUpdated: () => void;
  onAskMindMesh?: (prompt: string) => void;
}

export const TaskDetailModal: React.FC<TaskDetailModalProps> = ({
  task,
  token,
  onClose,
  onTaskUpdated,
  onAskMindMesh
}) => {
  const navigate = useNavigate();
  const [provenance, setProvenance] = useState<TaskProvenance | null>(null);
  const [isLoadingWhy, setIsLoadingWhy] = useState<boolean>(false);
  const [completionNote, setCompletionNote] = useState<string>('');
  const [isCompleting, setIsCompleting] = useState<boolean>(false);

  useEffect(() => {
    if (task) {
      setIsLoadingWhy(true);
      fetchTaskWhyProvenance(task.id, token)
        .then(setProvenance)
        .catch(err => console.error('Failed to load provenance:', err))
        .finally(() => setIsLoadingWhy(false));
    }
  }, [task, token]);

  if (!task) return null;

  const handleCompleteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCompleting(true);
    try {
      await completeTask(task.id, completionNote, token);
      onTaskUpdated();
      onClose();
    } catch (err) {
      console.error('Failed to complete task:', err);
    } finally {
      setIsCompleting(false);
    }
  };

  const handleAskHandoff = () => {
    const promptText = `What information is relevant to completing task "${task.title}"?`;
    if (onAskMindMesh) {
      onAskMindMesh(promptText);
    } else {
      navigate('/ask', { state: { initialPrompt: promptText } });
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-xl p-6 shadow-2xl space-y-5 text-slate-100 animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase font-mono">
                {task.task_type}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                STATUS: {task.status}
              </span>
              {task.is_ai_extracted && (
                <span className="text-[10px] font-mono text-indigo-400 font-bold px-1.5 py-0.5 bg-indigo-950 rounded flex items-center space-x-1">
                  <Sparkles className="w-3 h-3" />
                  <span>AI EXTRACTED</span>
                </span>
              )}
            </div>

            <h3 className="text-lg font-bold text-white mt-2">{task.title}</h3>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Description & Metadata */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Description</h4>
          <p className="text-xs text-slate-200 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800 leading-relaxed">
            {task.description}
          </p>
        </div>

        {/* Provenance Box ("Why do I have this task?") */}
        <div className="bg-gradient-to-br from-slate-950 via-indigo-950/40 to-slate-950 p-4 rounded-2xl border border-indigo-900/50 space-y-2">
          <div className="flex items-center space-x-2 text-indigo-300 text-xs font-bold">
            <HelpCircle className="w-4 h-4 text-indigo-400" />
            <span>Why Do I Have This Task?</span>
          </div>

          {isLoadingWhy ? (
            <p className="text-xs text-slate-400 font-mono">Tracing source knowledge...</p>
          ) : (
            <p className="text-xs text-slate-300 leading-relaxed">
              {provenance?.provenance_summary || 'Task provenance verified from workspace memory.'}
            </p>
          )}

          {provenance?.citations && provenance.citations.length > 0 && (
            <div className="pt-2 flex flex-wrap gap-2">
              {provenance.citations.map((c, i) => (
                <span
                  key={i}
                  className="inline-flex items-center space-x-1 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-300"
                >
                  <FileText className="w-3 h-3 text-indigo-400" />
                  <span>{c.title}</span>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Mark Complete Form */}
        {task.status !== 'COMPLETED' && (
          <form onSubmit={handleCompleteSubmit} className="space-y-3 pt-2 border-t border-slate-800">
            <h4 className="text-xs font-bold text-slate-300">Complete Task</h4>
            <input
              type="text"
              value={completionNote}
              onChange={(e) => setCompletionNote(e.target.value)}
              placeholder="Add optional completion note or verification outcome..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
            <button
              type="submit"
              disabled={isCompleting}
              className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-md flex items-center justify-center space-x-1.5"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Mark Completed</span>
            </button>
          </form>
        )}

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800">
          <button
            type="button"
            onClick={handleAskHandoff}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/40 text-xs font-semibold transition-all"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ask MindMesh</span>
          </button>

          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
