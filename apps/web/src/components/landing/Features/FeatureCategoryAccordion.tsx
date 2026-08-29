import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, CheckCircle2, Cpu, Database, Search, Zap, Users, ShieldCheck, Building } from 'lucide-react';
import { FeatureCategory } from './feature-data';
import { Badge } from '../foundation/feedback/Badge';

export interface FeatureCategoryAccordionProps {
  category: FeatureCategory;
  isExpanded: boolean;
  onToggle: () => void;
}

const ICON_MAP: Record<string, React.ReactNode> = {
  Cpu: <Cpu className="w-5 h-5 text-indigo-500" />,
  Database: <Database className="w-5 h-5 text-blue-500" />,
  Search: <Search className="w-5 h-5 text-cyan-500" />,
  Zap: <Zap className="w-5 h-5 text-amber-500" />,
  Users: <Users className="w-5 h-5 text-purple-500" />,
  ShieldCheck: <ShieldCheck className="w-5 h-5 text-emerald-500" />,
  Building: <Building className="w-5 h-5 text-indigo-500" />,
};

export const FeatureCategoryAccordion: React.FC<FeatureCategoryAccordionProps> = ({
  category,
  isExpanded,
  onToggle,
}) => {
  return (
    <div
      className={`
        rounded-ds-xl border transition-all duration-300 overflow-hidden text-left
        ${
          isExpanded
            ? 'bg-indigo-50/80 border-indigo-500/40 shadow-ds-medium dark:bg-slate-900/95'
            : 'bg-white/60 dark:bg-slate-900/60 border-slate-200/80 dark:border-slate-800/80 hover:border-slate-300 dark:hover:border-slate-700'
        }

      `.trim()}
    >
      {/* Accordion Header Trigger */}
      <button
        type="button"
        aria-expanded={isExpanded}
        aria-controls={`feature-panel-${category.id}`}
        onClick={onToggle}
        className="w-full flex items-center justify-between p-5 focus-ring text-left select-none"
      >
        <div className="flex items-center gap-3.5">
          <div
            className={`
              p-2.5 rounded-ds-lg transition-colors shrink-0
              ${isExpanded ? 'bg-indigo-500/20 text-indigo-400' : 'bg-slate-500/10 text-slate-400'}
            `.trim()}
          >
            {ICON_MAP[category.iconName] || <Cpu className="w-5 h-5" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-display font-bold text-base text-slate-900 dark:text-white">
                {category.title}
              </span>
              <Badge variant={isExpanded ? 'primary' : 'secondary'} className="text-[10px]">
                {category.badge}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1 font-medium">
              {category.summary}
            </p>
          </div>
        </div>

        <div
          className={`
            p-1.5 rounded-full transition-transform duration-300 shrink-0
            ${isExpanded ? 'rotate-180 bg-indigo-500/20 text-indigo-400' : 'text-slate-400'}
          `.trim()}
        >
          <ChevronDown className="w-4 h-4" />
        </div>
      </button>

      {/* Expandable Content Area */}
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            id={`feature-panel-${category.id}`}
            role="region"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.19, 1, 0.22, 1] }}
          >
            <div className="px-5 pb-6 pt-2 border-t border-slate-200/60 dark:border-slate-800/60 space-y-4">
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
                {category.description}
              </p>

              {/* Staggered Features List */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                {category.features.map((feat) => (
                  <div
                    key={feat.name}
                    className="p-3 rounded-ds-lg bg-slate-100/80 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 space-y-1"
                  >
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-900 dark:text-white">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                      <span>{feat.name}</span>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal pl-5">
                      {feat.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
