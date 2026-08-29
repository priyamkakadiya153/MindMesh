import React from 'react';
import { ShieldCheck, Zap, Lock, Cpu, Database, Network } from 'lucide-react';
import { Badge } from '../foundation/feedback/Badge';

export interface TrustMetric {
  value: string;
  label: string;
  sublabel: string;
  icon: React.ReactNode;
}

const TRUST_METRICS: TrustMetric[] = [
  {
    value: '0.04s',
    label: 'Semantic Query Speed',
    sublabel: 'Sub-second vector lookup',
    icon: <Zap className="w-4 h-4 text-amber-500" />,
  },
  {
    value: '100%',
    label: 'Organizational Memory',
    sublabel: 'Grounding chats & files',
    icon: <Database className="w-4 h-4 text-indigo-500" />,
  },
  {
    value: 'AES-256',
    label: 'Encrypted & SOC2 Ready',
    sublabel: 'Enterprise data safety',
    icon: <Lock className="w-4 h-4 text-emerald-500" />,
  },
  {
    value: 'Real-Time',
    label: 'Graph Intelligence',
    sublabel: 'Automatic task extraction',
    icon: <Network className="w-4 h-4 text-blue-500" />,
  },
];

export const HeroTrustIndicators: React.FC = () => {
  return (
    <div className="w-full space-y-6 pt-4">
      {/* Badges Bar */}
      <div className="flex flex-wrap items-center justify-center gap-2 mobile-sm:gap-3 text-xs">
        <Badge variant="secondary" icon={<ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />}>
          SOC2 Type II Ready
        </Badge>
        <Badge variant="secondary" icon={<Cpu className="w-3.5 h-3.5 text-indigo-500" />}>
          Zero Data Leakage RAG
        </Badge>
        <Badge variant="secondary" icon={<Lock className="w-3.5 h-3.5 text-blue-500" />}>
          End-to-End Encrypted
        </Badge>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mobile-sm:gap-4 max-w-4xl mx-auto p-4 rounded-ds-2xl bg-white/40 dark:bg-slate-900/40 border border-slate-200/80 dark:border-slate-800/80 backdrop-blur-md shadow-ds-soft">
        {TRUST_METRICS.map((metric) => (
          <div key={metric.label} className="flex flex-col items-center text-center p-2">
            <div className="flex items-center gap-1.5 mb-1">
              {metric.icon}
              <span className="font-display font-extrabold text-lg sm:text-xl tracking-tight text-slate-900 dark:text-white">
                {metric.value}
              </span>
            </div>
            <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
              {metric.label}
            </span>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
              {metric.sublabel}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
