import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  MessageSquare,
  Briefcase,
  Code,
  CheckCircle2,
  XCircle,
  Network,
  ArrowRight,
  Sparkles,
  Search,
  Database,
  Unlink,
} from 'lucide-react';
import { Badge } from '../foundation/feedback/Badge';
import { Button } from '../foundation/buttons/Button';
import { Heading, Text } from '../foundation/typography/Typography';

const DISCONNECTED_NODES = [
  { id: 'docs', name: 'Cloud Documents', icon: <FileText className="w-4 h-4 text-amber-500" />, app: 'Google Drive' },
  { id: 'chats', name: 'Chat History', icon: <MessageSquare className="w-4 h-4 text-purple-500" />, app: 'Slack / Teams' },
  { id: 'projects', name: 'Project Cards', icon: <Briefcase className="w-4 h-4 text-blue-500" />, app: 'Jira / Trello' },
  { id: 'code', name: 'Repository Code', icon: <Code className="w-4 h-4 text-emerald-500" />, app: 'GitHub / GitLab' },
];

export const DisconnectedKnowledgeIllustration: React.FC = () => {
  const [viewState, setViewState] = useState<'disconnected' | 'connected'>('disconnected');

  return (
    <div className="w-full max-w-4xl mx-auto p-6 sm:p-8 rounded-ds-2xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-ds-medium space-y-6 text-slate-900 dark:text-white">
      {/* Toggle View Controller */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Interactive Architectural Comparison
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            {viewState === 'disconnected'
              ? 'The Disconnected Reality of Fragmented Tools'
              : 'The MindMesh Unified Knowledge Core'}
          </h3>
        </div>

        {/* Toggle Switch Buttons */}
        <div className="flex items-center gap-1.5 p-1 rounded-ds-lg bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs">
          <button
            type="button"
            onClick={() => setViewState('disconnected')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-ds-md font-semibold transition-all ${
              viewState === 'disconnected'
                ? 'bg-rose-500/15 text-rose-600 dark:text-red-400 border border-rose-500/30'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Unlink className="w-3.5 h-3.5" />
            <span>Disconnected Tools</span>
          </button>
          <button
            type="button"
            onClick={() => setViewState('connected')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-ds-md font-semibold transition-all ${
              viewState === 'connected'
                ? 'bg-indigo-600 text-white shadow-ds-soft'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>MindMesh Unified Memory</span>
          </button>
        </div>
      </div>

      {/* Visual Canvas Diagram */}
      <AnimatePresence mode="wait">
        {viewState === 'disconnected' ? (
          <motion.div
            key="disconnected-view"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.25 }}
            className="space-y-6"
          >
            {/* Grid of Isolated Tools */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {DISCONNECTED_NODES.map((node) => (
                <div
                  key={node.id}
                  className="p-4 rounded-ds-xl bg-slate-50 dark:bg-slate-900/80 border border-rose-200 dark:border-red-500/30 relative text-center space-y-2 shadow-ds-soft"
                >
                  <div className="w-9 h-9 mx-auto rounded-full bg-rose-500/10 flex items-center justify-center">
                    {node.icon}
                  </div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-white">{node.name}</h4>
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-mono">{node.app}</span>
                  <div className="inline-flex items-center gap-1 text-[10px] text-rose-600 dark:text-red-400 font-semibold pt-1">
                    <XCircle className="w-3 h-3" /> Isolated Island
                  </div>
                </div>
              ))}
            </div>

            {/* Warning Callout Box */}
            <div className="p-4 rounded-ds-xl bg-rose-50/80 dark:bg-red-500/10 border border-rose-200 dark:border-red-500/20 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
              <div className="flex items-center gap-3 text-slate-700 dark:text-red-300">
                <Unlink className="w-5 h-5 text-rose-600 dark:text-red-400 shrink-0" />
                <span>
                  <strong className="text-rose-700 dark:text-red-300">Result:</strong> Search queries fail because no central vector index connects these silos. Information gets lost when team members leave.
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setViewState('connected')}
                className="shrink-0 text-rose-700 dark:text-red-300 border-rose-300 dark:border-red-500/40 hover:bg-rose-100 dark:hover:bg-red-500/10"
              >
                See Solution →
              </Button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="connected-view"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.25 }}
            className="space-y-6"
          >
            {/* MindMesh Core Connected Diagram */}
            <div className="relative p-6 rounded-ds-xl bg-gradient-to-br from-indigo-50/90 via-white to-purple-50/90 dark:from-indigo-950/60 dark:via-slate-900/80 dark:to-purple-950/60 border border-indigo-200 dark:border-indigo-500/40 shadow-ds-glow text-center space-y-6">
              {/* Core Hub Badge */}
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-ds-pill bg-indigo-600 text-white text-xs font-bold shadow-ds-hero">
                <Network className="w-4 h-4 animate-spin-slow" />
                <span>MindMesh Knowledge Intelligence Core</span>
              </div>

              {/* Connected Peripheral Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
                {DISCONNECTED_NODES.map((node) => (
                  <div
                    key={node.id}
                    className="p-3 rounded-ds-lg bg-white dark:bg-slate-900/90 border border-indigo-200 dark:border-indigo-500/30 text-center space-y-1.5 shadow-ds-soft"
                  >
                    <div className="w-7 h-7 mx-auto rounded-full bg-indigo-500/10 dark:bg-indigo-500/20 flex items-center justify-center">
                      {node.icon}
                    </div>
                    <span className="text-xs font-bold text-slate-900 dark:text-white block">{node.name}</span>
                    <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center justify-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Indexed
                    </span>
                  </div>
                ))}
              </div>

              <p className="text-xs text-slate-600 dark:text-indigo-200 max-w-xl mx-auto leading-relaxed font-medium">
                MindMesh automatically indexes every conversation, document, decision, and project task into a single, searchable semantic graph.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>

  );
};
