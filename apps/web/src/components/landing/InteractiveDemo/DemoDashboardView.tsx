import React from 'react';
import {
  Briefcase,
  FileText,
  MessageSquare,
  CheckCircle,
  Network,
  Clock,
  Sparkles,
  ArrowUpRight,
  Eye,
} from 'lucide-react';
import { Badge } from '../foundation/feedback/Badge';
import { Card } from '../foundation/layout/Card';
import { DemoDoc } from './DemoDocPreviewModal';

export interface WorkspaceData {
  name: string;
  projectsCount: number;
  documentsCount: number;
  decisionsCount: number;
  recentDocs: DemoDoc[];
  activities: Array<{ id: string; action: string; time: string; user: string }>;
}

export interface DemoDashboardViewProps {
  workspace: WorkspaceData;
  onPreviewDoc: (doc: DemoDoc) => void;
}

export const DemoDashboardView: React.FC<DemoDashboardViewProps> = ({
  workspace,
  onPreviewDoc,
}) => {
  return (
    <div className="space-y-6 text-left">
      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mobile-sm:gap-4">
        <Card elevation="soft" padding="sm" className="bg-white dark:bg-slate-900/80 border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Projects Roster</span>
            <Briefcase className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-display font-extrabold text-xl text-slate-900 dark:text-white">
              {workspace.projectsCount}
            </span>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">Active</span>
          </div>
        </Card>

        <Card elevation="soft" padding="sm" className="bg-white dark:bg-slate-900/80 border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Indexed Docs</span>
            <FileText className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-display font-extrabold text-xl text-slate-900 dark:text-white">
              {workspace.documentsCount}
            </span>
            <span className="text-[10px] text-indigo-600 dark:text-indigo-400 font-semibold">Parsed</span>
          </div>
        </Card>

        <Card elevation="soft" padding="sm" className="bg-white dark:bg-slate-900/80 border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Extracted Decisions</span>
            <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-display font-extrabold text-xl text-slate-900 dark:text-white">
              {workspace.decisionsCount}
            </span>
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">In Graph</span>
          </div>
        </Card>

        <Card elevation="soft" padding="sm" className="bg-white dark:bg-slate-900/80 border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Vector Speed</span>
            <Sparkles className="w-4 h-4 text-purple-600 dark:text-purple-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-display font-extrabold text-xl text-slate-900 dark:text-white">0.04s</span>
            <span className="text-[10px] text-purple-600 dark:text-purple-400 font-semibold">Sub-second</span>
          </div>
        </Card>
      </div>

      {/* Main Grid: Recent Documents & Real-Time Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Recent Knowledge Documents (8 cols) */}
        <div className="lg:col-span-8 p-5 rounded-ds-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
            <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> Recent Knowledge Documents
            </h4>
            <span className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold font-mono">
              Workspace: {workspace.name}
            </span>
          </div>

          <div className="space-y-2">
            {workspace.recentDocs.map((doc) => (
              <div
                key={doc.id}
                className="p-3 rounded-ds-lg bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80 hover:border-indigo-500/40 transition-all flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0" />
                  <div>
                    <span className="font-bold text-slate-900 dark:text-white block">{doc.name}</span>
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block font-mono">
                      {doc.size} • Author: {doc.author}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => onPreviewDoc(doc)}
                  className="flex items-center gap-1 px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-600 dark:text-indigo-300 border border-indigo-500/20 hover:bg-indigo-500/20 transition-all text-[11px] font-semibold"
                >
                  <Eye className="w-3 h-3" /> Preview
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Real-time Activity Feed (4 cols) */}
        <div className="lg:col-span-4 p-5 rounded-ds-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-4">
          <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2 pb-3 border-b border-slate-200 dark:border-slate-800">
            <Clock className="w-4 h-4 text-cyan-600 dark:text-cyan-400" /> Activity Stream
          </h4>

          <div className="space-y-3">
            {workspace.activities.map((act) => (
              <div key={act.id} className="text-xs space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-semibold text-indigo-600 dark:text-indigo-300">{act.user}</span>
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">{act.time}</span>
                </div>
                <p className="text-slate-600 dark:text-slate-300 text-[11px] leading-relaxed">{act.action}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>

  );
};
