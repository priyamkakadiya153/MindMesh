import React from 'react';
import { Sparkles, Calendar, Briefcase, FileText, Users } from 'lucide-react';

interface WelcomeBannerProps {
  userName?: string;
  workspaceName?: string;
  projectsCount: number;
  documentsCount: number;
  membersCount: number;
}

export function WelcomeBanner({
  userName = 'User',
  workspaceName = 'Engineering Workspace',
  projectsCount,
  documentsCount,
  membersCount
}: WelcomeBannerProps) {
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-700 to-purple-700 dark:from-indigo-900/80 dark:via-indigo-950/60 dark:to-slate-950 border border-indigo-500/20 p-4 sm:p-5 md:p-6 text-white shadow-xl shadow-indigo-600/10">
      {/* Decorative background glow */}
      <div className="absolute top-0 right-0 -mt-12 -mr-12 w-64 h-64 bg-white/10 dark:bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-1/3 -mb-16 w-80 h-80 bg-purple-400/20 dark:bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-200 dark:text-indigo-400 text-xs font-semibold tracking-wider uppercase mb-0.5">
            <Sparkles size={14} className="animate-pulse" />
            <span>Workspace Hub</span>
          </div>
          <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-tight mb-1">
            {greeting}, {userName} 👋
          </h1>
          <p className="text-indigo-100 dark:text-gray-300 text-xs max-w-xl leading-relaxed">
            Welcome back to <span className="text-white font-semibold underline decoration-indigo-300/40">{workspaceName}</span>. 
            All files, conversations, and project items have been parsed and indexed.
          </p>
        </div>

        {/* Dynamic Metrics Badge Roster */}
        <div className="flex flex-wrap gap-3 shrink-0">
          <div className="px-3.5 py-2 bg-white/10 dark:bg-black/20 border border-white/20 dark:border-white/10 rounded-xl backdrop-blur-md flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-white/20 text-white dark:bg-indigo-500/20 dark:text-indigo-300">
              <Briefcase size={15} />
            </div>
            <div>
              <div className="text-base font-bold text-white leading-none">{projectsCount}</div>
              <div className="text-[9px] text-indigo-100 dark:text-gray-400 font-medium uppercase mt-0.5">Active Projects</div>
            </div>
          </div>

          <div className="px-3.5 py-2 bg-white/10 dark:bg-black/20 border border-white/20 dark:border-white/10 rounded-xl backdrop-blur-md flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-white/20 text-white dark:bg-purple-500/20 dark:text-purple-300">
              <FileText size={15} />
            </div>
            <div>
              <div className="text-base font-bold text-white leading-none">{documentsCount}</div>
              <div className="text-[9px] text-indigo-100 dark:text-gray-400 font-medium uppercase mt-0.5">Documents</div>
            </div>
          </div>

          <div className="px-3.5 py-2 bg-white/10 dark:bg-black/20 border border-white/20 dark:border-white/10 rounded-xl backdrop-blur-md flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-white/20 text-white dark:bg-emerald-500/20 dark:text-emerald-300">
              <Users size={15} />
            </div>
            <div>
              <div className="text-base font-bold text-white leading-none">{membersCount}</div>
              <div className="text-[9px] text-indigo-100 dark:text-gray-400 font-medium uppercase mt-0.5">Team Members</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
