import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  FileText,
  Briefcase,
  MessageSquare,
  Users,
  CheckCircle,
  Clock,
  ArrowRight,
} from 'lucide-react';
import { GraphNode } from './graph-dataset';
import { Badge } from '../foundation/feedback/Badge';

export interface AIContextPanelProps {
  node: GraphNode;
  onClose?: () => void;
}

export const AIContextPanel: React.FC<AIContextPanelProps> = ({ node }) => {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={node.id}
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -12 }}
        transition={{ duration: 0.25 }}
        className="p-5 rounded-ds-2xl bg-white dark:bg-slate-950/95 border border-indigo-200 dark:border-indigo-500/40 shadow-ds-modal text-slate-900 dark:text-white text-left space-y-4 backdrop-blur-xl"
      >
        {/* Node Title & Type Badge */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
            <span className="font-bold text-sm text-slate-900 dark:text-white line-clamp-1">{node.title}</span>
          </div>
          <Badge variant="primary" className="text-[9px] uppercase font-mono shrink-0">
            {node.type}
          </Badge>
        </div>

        {/* Connected Items Metric Grid */}
        <div className="grid grid-cols-5 gap-1.5 text-center">
          <div className="p-1.5 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400 text-xs block">
              {node.stats.projects}
            </span>
            <span className="text-[9px] text-slate-500 dark:text-slate-400 block font-sans">Projects</span>
          </div>
          <div className="p-1.5 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <span className="font-mono font-bold text-cyan-600 dark:text-cyan-400 text-xs block">
              {node.stats.conversations}
            </span>
            <span className="text-[9px] text-slate-500 dark:text-slate-400 block font-sans">Chats</span>
          </div>
          <div className="p-1.5 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <span className="font-mono font-bold text-purple-600 dark:text-purple-400 text-xs block">
              {node.stats.meetings}
            </span>
            <span className="text-[9px] text-slate-500 dark:text-slate-400 block font-sans">Meetings</span>
          </div>
          <div className="p-1.5 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400 text-xs block">
              {node.stats.tasks}
            </span>
            <span className="text-[9px] text-slate-500 dark:text-slate-400 block font-sans">Tasks</span>
          </div>
          <div className="p-1.5 rounded bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <span className="font-mono font-bold text-amber-600 dark:text-amber-400 text-xs block">
              {node.stats.people}
            </span>
            <span className="text-[9px] text-slate-500 dark:text-slate-400 block font-sans">People</span>
          </div>
        </div>

        {/* AI Summary Description */}
        <div className="p-3.5 rounded-ds-xl bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-500/30 space-y-1.5">
          <span className="text-[10px] uppercase font-bold text-indigo-600 dark:text-indigo-300 tracking-wider block">
            AI Graph Synthesis:
          </span>
          <p className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed">{node.summary}</p>
        </div>

        {/* Workspace Tag */}
        <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 pt-1 font-mono">
          <span>Workspace: {node.workspace}</span>
          <span className="text-indigo-600 dark:text-indigo-400 font-semibold">{node.connectedIds.length} Linked Nodes</span>
        </div>
      </motion.div>

    </AnimatePresence>
  );
};
