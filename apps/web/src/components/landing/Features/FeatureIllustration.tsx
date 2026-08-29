import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Cpu,
  Database,
  Search,
  Zap,
  Users,
  ShieldCheck,
  Building,
  Sparkles,
  CheckCircle2,
  FileText,
  Lock,
  Network,
} from 'lucide-react';
import { FeatureCategory } from './feature-data';
import { Badge } from '../foundation/feedback/Badge';

export interface FeatureIllustrationProps {
  category: FeatureCategory;
}

export const FeatureIllustration: React.FC<FeatureIllustrationProps> = ({ category }) => {
  return (
    <div className="w-full h-full p-6 sm:p-8 rounded-ds-2xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 shadow-ds-hero text-slate-900 dark:text-white flex flex-col justify-between relative overflow-hidden min-h-[380px]">
      {/* Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 rounded-full bg-indigo-600/10 blur-3xl pointer-events-none" />

      <AnimatePresence mode="wait">
        <motion.div
          key={category.id}
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.96 }}
          transition={{ duration: 0.3 }}
          className="space-y-6 relative z-10 flex flex-col h-full justify-between"
        >
          {/* Category Top Indicator */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2 text-xs font-bold text-indigo-600 dark:text-indigo-400">
              <Sparkles className="w-4 h-4" />
              <span className="uppercase tracking-wider font-mono">{category.title} Capability</span>
            </div>
            <Badge variant="primary" className="text-[10px]">
              {category.badge}
            </Badge>
          </div>

          {/* Dynamic Graphic View based on Category */}
          <div className="my-auto space-y-4">
            {category.id === 'ai-intelligence' && (
              <div className="p-4 rounded-ds-xl bg-indigo-50/80 dark:bg-gradient-to-br dark:from-indigo-950/60 dark:to-purple-950/60 border border-indigo-200 dark:border-indigo-500/30 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> RAG Synthesis Pipeline
                  </span>
                  <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">100% Grounded</span>
                </div>
                <p className="text-xs text-slate-700 dark:text-slate-200 leading-relaxed font-sans">
                  "JWT Refresh tokens persist for 30 days with sliding session duration as decided in architecture sync."
                </p>
                <div className="pt-2 border-t border-indigo-200 dark:border-slate-800 flex items-center gap-2 text-[10px] text-indigo-700 dark:text-indigo-300 font-mono font-medium">
                  <FileText className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" /> Cited: architecture_sync_august_2026.md
                </div>
              </div>
            )}

            {category.id === 'knowledge-management' && (
              <div className="p-4 rounded-ds-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs font-bold text-slate-900 dark:text-white">
                  <span className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-blue-600 dark:text-blue-400" /> Universal Metadata Extractor
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400">Auto Indexing</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="p-2 rounded bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-300 font-medium">
                    PDF Document → 45 Chunks
                  </div>
                  <div className="p-2 rounded bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-300 font-medium">
                    Markdown → 18 Vector Nodes
                  </div>
                </div>
              </div>
            )}

            {category.id === 'universal-search' && (
              <div className="p-4 rounded-ds-xl bg-white dark:bg-slate-900/90 border border-indigo-200 dark:border-indigo-500/40 space-y-3 shadow-ds-glow">
                <div className="flex items-center justify-between text-xs font-bold text-slate-900 dark:text-white">
                  <span className="flex items-center gap-2">
                    <Search className="w-4 h-4 text-cyan-600 dark:text-cyan-400" /> Semantic Vector Engine
                  </span>
                  <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">0.04s Speed</span>
                </div>
                <div className="p-2.5 rounded bg-indigo-50/80 dark:bg-slate-950 border border-indigo-200 dark:border-slate-800 text-xs font-mono text-indigo-700 dark:text-indigo-300">
                  Query: "What is our SOC2 encryption standard?"
                </div>
                <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Result: AES-256 at rest & TLS 1.3 in transit
                </div>
              </div>
            )}

            {category.id === 'automation' && (
              <div className="p-4 rounded-ds-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs font-bold text-slate-900 dark:text-white">
                  <span className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-amber-600 dark:text-amber-400" /> Decision Extraction Engine
                  </span>
                  <Badge variant="success" className="text-[9px]">Auto Trigger</Badge>
                </div>
                <div className="p-2.5 rounded bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-800 dark:text-slate-200 font-medium">
                  Extracted Task: Enforce single-device session revocation endpoint.
                </div>
              </div>
            )}

            {category.id === 'collaboration' && (
              <div className="p-4 rounded-ds-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs font-bold text-slate-900 dark:text-white">
                  <span className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-purple-600 dark:text-purple-400" /> Team Collaboration Stream
                  </span>
                  <span className="text-[10px] font-mono text-indigo-600 dark:text-indigo-400 font-bold">Real-Time</span>
                </div>
                <div className="p-2.5 rounded bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-800 dark:text-slate-300 font-medium">
                  Engineering R&D Workspace: 14 Projects synchronized across 12 members.
                </div>
              </div>
            )}

            {category.id === 'security' && (
              <div className="p-4 rounded-ds-xl bg-white dark:bg-slate-900/90 border border-emerald-200 dark:border-emerald-500/30 space-y-3">
                <div className="flex items-center justify-between text-xs font-bold text-slate-900 dark:text-white">
                  <span className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" /> SOC2 Type II Matrix
                  </span>
                  <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">AES-256 Verified</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-slate-800 dark:text-slate-300 font-medium">
                  <div className="p-2 rounded bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">RBAC Enforced</div>
                  <div className="p-2 rounded bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800">Tenant Isolation</div>
                </div>
              </div>
            )}

            {category.id === 'enterprise' && (
              <div className="p-4 rounded-ds-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs font-bold text-slate-900 dark:text-white">
                  <span className="flex items-center gap-2">
                    <Building className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> Multi-Tenant Scale
                  </span>
                  <span className="text-[10px] font-mono text-indigo-600 dark:text-indigo-300 font-bold">Unlimited Seats</span>
                </div>
                <div className="p-2.5 rounded bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-xs text-slate-800 dark:text-slate-300 font-medium">
                  Centralized organization management with 99.9% Uptime SLA.
                </div>
              </div>
            )}
          </div>

          {/* Metric Footer */}
          <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs">
            <span className="text-slate-500 dark:text-slate-400 font-medium">{category.metricLabel}</span>
            <span className="font-mono font-extrabold text-indigo-600 dark:text-indigo-400">{category.metricValue}</span>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

