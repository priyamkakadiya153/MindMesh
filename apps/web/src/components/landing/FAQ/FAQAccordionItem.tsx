import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { FAQItem } from './faq-dataset';
import { Badge } from '../foundation/feedback/Badge';

export interface FAQAccordionItemProps {
  item: FAQItem;
  isOpen: boolean;
  onToggle: () => void;
}

export const FAQAccordionItem: React.FC<FAQAccordionItemProps> = ({
  item,
  isOpen,
  onToggle,
}) => {
  return (
    <div className="rounded-ds-xl border border-slate-200/80 dark:border-slate-800 bg-white/60 dark:bg-slate-900/60 overflow-hidden transition-all text-left">
      <button
        type="button"
        aria-expanded={isOpen}
        aria-controls={`faq-panel-${item.id}`}
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 focus-ring text-left font-bold text-xs sm:text-sm text-slate-900 dark:text-white"
      >
        <div className="flex items-center gap-3">
          <Badge variant="secondary" className="text-[9px] uppercase font-mono shrink-0">
            {item.categoryLabel}
          </Badge>
          <span>{item.question}</span>
        </div>
        <ChevronDown
          className={`w-4 h-4 text-slate-400 transition-transform duration-300 shrink-0 ml-2 ${
            isOpen ? 'rotate-180 text-indigo-400' : ''
          }`}
        />
      </button>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            id={`faq-panel-${item.id}`}
            role="region"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.19, 1, 0.22, 1] }}
          >
            <div className="px-4 pb-4 pt-1 text-xs text-slate-600 dark:text-slate-300 leading-relaxed border-t border-slate-200/60 dark:border-slate-800/60">
              {item.answer}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
