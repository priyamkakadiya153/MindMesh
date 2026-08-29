import React from 'react';
import { TaskItem } from '../task-api';
import {
  CheckCircle2, Clock, AlertTriangle, UserCheck, Sparkles, HelpCircle,
  Briefcase, ArrowUpRight, Flame
} from 'lucide-react';

interface TaskCardProps {
  task: TaskItem;
  onSelect: (task: TaskItem) => void;
  onComplete: (taskId: string, e: React.MouseEvent) => void;
  onAskMindMesh?: (prompt: string) => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onSelect,
  onComplete,
  onAskMindMesh
}) => {
  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'COMPLETED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">COMPLETED</span>;
      case 'IN_PROGRESS':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20">IN PROGRESS</span>;
      case 'BLOCKED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center space-x-1"><AlertTriangle className="w-2.5 h-2.5" /><span>BLOCKED</span></span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">TODO</span>;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority.toUpperCase()) {
      case 'URGENT':
      case 'HIGH':
        return <span className="text-[10px] font-mono font-bold text-amber-400 flex items-center space-x-0.5"><Flame className="w-3 h-3" /><span>HIGH</span></span>;
      default:
        return <span className="text-[10px] font-mono text-slate-400">MED</span>;
    }
  };

  const handleAskWhy = (e: React.MouseEvent) => {
    e.stopPropagation();
    const promptText = `Why do I have the task "${task.title}" and what is its decision background?`;
    if (onAskMindMesh) {
      onAskMindMesh(promptText);
    }
  };

  return (
    <div
      onClick={() => onSelect(task)}
      className="p-4 bg-slate-900/70 border border-slate-800 hover:border-indigo-500/50 hover:bg-slate-800/60 rounded-2xl cursor-pointer transition-all space-y-3 shadow-md group"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={(e) => onComplete(task.id, e)}
            className={`p-1 rounded-lg border transition-colors ${
              task.status === 'COMPLETED'
                ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400'
                : 'bg-slate-800 border-slate-700 text-slate-500 hover:text-emerald-400 hover:border-emerald-500/50'
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
          </button>

          {getStatusBadge(task.status)}
          {task.is_ai_extracted && (
            <span className="text-[9px] font-mono font-bold uppercase text-indigo-400 px-1.5 py-0.5 bg-indigo-950 rounded border border-indigo-800/60 flex items-center space-x-1">
              <Sparkles className="w-2.5 h-2.5" />
              <span>AI</span>
            </span>
          )}
        </div>

        {getPriorityBadge(task.priority)}
      </div>

      <div>
        <h4 className="text-sm font-bold text-slate-100 group-hover:text-indigo-300 transition-colors line-clamp-1">
          {task.title}
        </h4>
        <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
          {task.description}
        </p>
      </div>

      <div className="flex items-center justify-between pt-1 text-[11px] border-t border-slate-800/80">
        <div className="flex items-center space-x-2 text-slate-400">
          {task.due_date && (
            <span className="flex items-center space-x-1 text-slate-400 font-mono text-[10px]">
              <Clock className="w-3 h-3 text-slate-500" />
              <span>{task.due_date.slice(0, 10)}</span>
            </span>
          )}
          {task.assignee_id && (
            <span className="flex items-center space-x-1 text-slate-300">
              <UserCheck className="w-3 h-3 text-indigo-400" />
              <span>Assigned</span>
            </span>
          )}
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            type="button"
            onClick={handleAskWhy}
            className="flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-800 hover:bg-indigo-950 text-indigo-300 border border-slate-700 text-[10px] font-medium transition-all"
          >
            <HelpCircle className="w-3 h-3" />
            <span>Why?</span>
          </button>
        </div>
      </div>
    </div>
  );
};
