import React from 'react';
import { Sparkles, Search, FileText, CheckCircle2, Bot, Layers } from 'lucide-react';
import { FloatingElement } from '../foundation/motion/MotionWrappers';
import { Card } from '../foundation/layout/Card';
import { Badge } from '../foundation/feedback/Badge';

export const HeroFloatingCardsDesktop: React.FC = () => {
  return (
    <>
      {/* Top Left Floating Card: AI Vector Search */}
      <FloatingElement
        distance={12}
        duration={5}
        className="hidden lg:block absolute -top-8 -left-12 z-20 w-64 pointer-events-auto"
      >
        <Card elevation="floating" padding="sm" className="border-indigo-200 dark:border-indigo-500/30 bg-white dark:bg-slate-950/80 backdrop-blur-xl shadow-ds-medium">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-ds-lg bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 shrink-0">
              <Search className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-bold text-slate-900 dark:text-white">Semantic Search</span>
                <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">0.04s</span>
              </div>
              <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5 line-clamp-1 font-medium">
                "Where is the Q3 architecture RFC?"
              </p>
              <div className="mt-2 flex items-center gap-1.5 text-[10px] text-indigo-600 dark:text-indigo-300 font-semibold">
                <Sparkles className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
                <span>3 vector matches found</span>
              </div>
            </div>
          </div>
        </Card>
      </FloatingElement>

      {/* Top Right Floating Card: Automatic Task & Decision Extraction */}
      <FloatingElement
        distance={14}
        duration={6}
        className="hidden lg:block absolute -top-6 -right-10 z-20 w-64 pointer-events-auto"
      >
        <Card elevation="floating" padding="sm" className="border-emerald-200 dark:border-emerald-500/30 bg-white dark:bg-slate-950/80 backdrop-blur-xl shadow-ds-medium">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-ds-lg bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 shrink-0">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900 dark:text-white">Decision Graph</span>
                <Badge variant="success" className="text-[9px] px-1.5 py-0">Auto</Badge>
              </div>
              <p className="text-[11px] text-slate-800 dark:text-slate-300 font-semibold mt-1">
                Approve JWT Refresh Token Spec
              </p>
              <span className="text-[10px] text-slate-500 block mt-0.5 font-medium">
                Extracted from Architecture Sync
              </span>
            </div>
          </div>
        </Card>
      </FloatingElement>

      {/* Bottom Left Floating Card: Smart Document RAG */}
      <FloatingElement
        distance={10}
        duration={7}
        className="hidden lg:block absolute -bottom-8 -left-10 z-20 w-60 pointer-events-auto"
      >
        <Card elevation="floating" padding="sm" className="border-cyan-200 dark:border-cyan-500/30 bg-white dark:bg-slate-950/80 backdrop-blur-xl shadow-ds-medium">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-ds-lg bg-cyan-50 dark:bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 shrink-0">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-900 dark:text-white block">Document Parsing</span>
              <span className="text-[10px] text-slate-600 dark:text-slate-400 block mt-0.5 font-medium">
                PDF, MD, Code & Slides indexed
              </span>
            </div>
          </div>
        </Card>
      </FloatingElement>

      {/* Bottom Right Floating Card: AI Assistant Grounded */}
      <FloatingElement
        distance={16}
        duration={5.5}
        className="hidden lg:block absolute -bottom-6 -right-8 z-20 w-64 pointer-events-auto"
      >
        <Card elevation="floating" padding="sm" className="border-purple-200 dark:border-purple-500/30 bg-white dark:bg-slate-950/80 backdrop-blur-xl shadow-ds-medium">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-ds-lg bg-purple-50 dark:bg-purple-500/10 text-purple-600 dark:text-purple-400 shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <span className="text-xs font-bold text-slate-900 dark:text-white block">AI Assistant Grounded</span>
              <span className="text-[10px] text-indigo-700 dark:text-indigo-300 font-semibold block mt-0.5">
                100% cited workspace sources
              </span>
            </div>
          </div>
        </Card>
      </FloatingElement>
    </>
  );
};

export const HeroFloatingCardsMobile: React.FC = () => {
  return (
    <div className="grid grid-cols-2 gap-2 mt-4 lg:hidden">
      <div className="p-3 rounded-ds-lg bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 text-left">
        <div className="flex items-center gap-1.5 text-indigo-600 dark:text-indigo-400 text-xs font-bold">
          <Search className="w-3.5 h-3.5" />
          <span>Semantic Search</span>
        </div>
        <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 block">0.04s vector lookup</span>
      </div>

      <div className="p-3 rounded-ds-lg bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 text-left">
        <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 text-xs font-bold">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Decision Extraction</span>
        </div>
        <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 block">Automatic task graphs</span>
      </div>
    </div>
  );
};

