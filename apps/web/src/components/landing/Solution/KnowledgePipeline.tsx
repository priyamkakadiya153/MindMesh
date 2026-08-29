import React from 'react';
import { motion } from 'framer-motion';
import { UploadCloud, Layers, Cpu, Search, Zap, ChevronRight } from 'lucide-react';

export interface PipelineStep {
  id: number;
  key: string;
  name: string;
  subtitle: string;
  icon: React.ReactNode;
}

export const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: 1,
    key: 'capture',
    name: '1. Capture',
    subtitle: 'Files, Chats & Notes',
    icon: <UploadCloud className="w-5 h-5" />,
  },
  {
    id: 2,
    key: 'organize',
    name: '2. Organize',
    subtitle: 'Workspaces & Projects',
    icon: <Layers className="w-5 h-5" />,
  },
  {
    id: 3,
    key: 'understand',
    name: '3. Understand',
    subtitle: 'AI Vector & Graph Engine',
    icon: <Cpu className="w-5 h-5" />,
  },
  {
    id: 4,
    key: 'retrieve',
    name: '4. Retrieve',
    subtitle: '0.04s Natural Search',
    icon: <Search className="w-5 h-5" />,
  },
  {
    id: 5,
    key: 'act',
    name: '5. Act',
    subtitle: 'Grounded Decisions',
    icon: <Zap className="w-5 h-5" />,
  },
];

export interface KnowledgePipelineProps {
  activeStep: number;
  onSelectStep: (stepId: number) => void;
}

export const KnowledgePipeline: React.FC<KnowledgePipelineProps> = ({
  activeStep,
  onSelectStep,
}) => {
  return (
    <div className="w-full space-y-6">
      {/* Desktop Horizontal Animated Pipeline */}
      <div className="hidden md:flex items-center justify-between relative max-w-5xl mx-auto px-4">
        {/* Connecting Animated Line Background */}
        <div className="absolute top-1/2 left-8 right-8 -translate-y-1/2 h-1 bg-slate-200 dark:bg-slate-800 rounded-full -z-0">
          <motion.div
            className="h-full bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 rounded-full"
            initial={{ width: '0%' }}
            animate={{ width: `${((activeStep - 1) / (PIPELINE_STEPS.length - 1)) * 100}%` }}
            transition={{ duration: 0.4, ease: 'easeInOut' }}
          />
        </div>

        {/* Step Nodes */}
        {PIPELINE_STEPS.map((step) => {
          const isActive = activeStep === step.id;
          const isPassed = activeStep > step.id;

          return (
            <button
              key={step.id}
              type="button"
              onClick={() => onSelectStep(step.id)}
              className="relative z-10 flex flex-col items-center group focus-ring rounded-ds-lg p-2"
            >
              <div
                className={`
                  w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 shadow-ds-medium
                  ${
                    isActive
                      ? 'bg-indigo-600 text-white ring-4 ring-indigo-500/30 scale-110 shadow-ds-glow'
                      : isPassed
                      ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-500/40'
                      : 'bg-white dark:bg-slate-900 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                  }
                `.trim()}
              >
                {step.icon}
              </div>

              <div className="mt-3 text-center">
                <span
                  className={`text-xs font-bold block transition-colors ${
                    isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-700 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-white'
                  }`}
                >
                  {step.name}
                </span>
                <span className="text-[10px] text-slate-500 block">{step.subtitle}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Mobile Vertical & Carousel Stepper */}
      <div className="flex md:hidden items-center gap-2 overflow-x-auto no-scrollbar pb-2 px-2">
        {PIPELINE_STEPS.map((step) => {
          const isActive = activeStep === step.id;

          return (
            <button
              key={step.id}
              type="button"
              onClick={() => onSelectStep(step.id)}
              className={`
                flex items-center gap-2 px-3 py-2 rounded-ds-lg border shrink-0 text-xs font-semibold transition-all
                ${
                  isActive
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-ds-soft'
                    : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-400 border-slate-200 dark:border-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }
              `.trim()}
            >

              {step.icon}
              <span>{step.name}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
