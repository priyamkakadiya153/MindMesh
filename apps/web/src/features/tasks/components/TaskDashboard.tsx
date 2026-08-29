import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchTasks, createManualTask, completeTask, TaskItem } from '../task-api';
import { TaskCard } from './TaskCard';
import { TaskDetailModal } from './TaskDetailModal';
import {
  CheckSquare, Plus, Search, Filter, Loader2, RefreshCw,
  Sparkles, Clock, AlertTriangle, Layers, UserCheck
} from 'lucide-react';

interface TaskDashboardProps {
  organizationId?: string;
  workspaceId?: string;
  token?: string;
  onAskMindMesh?: (prompt: string) => void;
}

export const TaskDashboard: React.FC<TaskDashboardProps> = ({
  organizationId,
  workspaceId,
  token,
  onAskMindMesh
}) => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedTask, setSelectedTask] = useState<TaskItem | null>(null);

  // New task modal
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [newTitle, setNewTitle] = useState<string>('');
  const [newDesc, setNewDesc] = useState<string>('');

  const loadTasks = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchTasks({
        workspaceId,
        status: statusFilter !== 'all' ? statusFilter : undefined
      }, token);
      setTasks(data);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, statusFilter, token]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  const handleQuickComplete = async (taskId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await completeTask(taskId, undefined, token);
      loadTasks();
    } catch (err) {
      console.error('Failed to complete task:', err);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newDesc.trim()) return;
    try {
      await createManualTask({
        title: newTitle,
        description: newDesc,
        workspaceId
      }, token);
      setNewTitle('');
      setNewDesc('');
      setIsCreating(false);
      loadTasks();
    } catch (err) {
      console.error('Failed to create task:', err);
    }
  };

  const filteredTasks = tasks.filter(t => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return t.title.toLowerCase().includes(q) || t.description.toLowerCase().includes(q);
  });

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 select-none">
      
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4 backdrop-blur-md">
        <div>
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
            ACTIONABLE KNOWLEDGE
          </span>
          <h1 className="text-2xl font-black text-white mt-1 flex items-center space-x-2">
            <CheckSquare className="w-7 h-7 text-indigo-400" />
            <span>Task Intelligence</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Traceable tasks derived from workspace decisions, conversations, and documents.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsCreating(true)}
          className="flex items-center space-x-1.5 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg transition-all self-start md:self-auto shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>New Task</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter tasks..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        <div className="flex items-center space-x-2 overflow-x-auto w-full sm:w-auto scrollbar-none">
          {['all', 'TODO', 'IN_PROGRESS', 'BLOCKED', 'COMPLETED', 'OVERDUE'].map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1 rounded-xl text-xs font-semibold uppercase transition-all whitespace-nowrap ${
                statusFilter === st
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-950 text-slate-400 hover:bg-slate-800 border border-slate-800'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Task Grid */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-3">
          <Loader2 className="w-7 h-7 animate-spin text-indigo-400" />
          <span className="text-xs font-medium">Loading task intelligence...</span>
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="p-12 text-center text-slate-400 text-xs bg-slate-900/40 border border-slate-800 rounded-3xl space-y-2">
          <CheckSquare className="w-10 h-10 text-slate-600 mx-auto stroke-1" />
          <p className="font-semibold">No tasks found matching current filter.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTasks.map((t) => (
            <TaskCard
              key={t.id}
              task={t}
              onSelect={setSelectedTask}
              onComplete={handleQuickComplete}
              onAskMindMesh={onAskMindMesh}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      {isCreating && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <form onSubmit={handleCreateTask} className="bg-slate-900 border border-slate-800 p-6 rounded-3xl w-full max-w-md space-y-4 text-slate-100 shadow-2xl">
            <h3 className="text-base font-bold text-white">Create Manual Task</h3>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Task Title..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              required
            />
            <textarea
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              placeholder="Task Description..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 h-24"
              required
            />
            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setIsCreating(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold"
              >
                Create Task
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Task Detail Modal */}
      <TaskDetailModal
        task={selectedTask}
        token={token}
        onClose={() => setSelectedTask(null)}
        onTaskUpdated={loadTasks}
        onAskMindMesh={onAskMindMesh}
      />
    </div>
  );
};
