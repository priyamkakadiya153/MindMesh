import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, HelpCircle } from 'lucide-react';
import { PRICING_FAQS } from './pricing-data';

export const PricingFAQAccordion: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggleIndex = (idx: number) => {
    setOpenIndex(openIndex === idx ? null : idx);
  };

  return (
    <div className="space-y-4 max-w-3xl mx-auto text-left">
      <div className="text-center space-y-1">
        <h4 className="font-display font-extrabold text-xl text-slate-900 dark:text-white">
          Frequently Asked Questions
        </h4>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Everything you need to know about MindMesh plans, billing, and trial access.
        </p>
      </div>

      <div className="space-y-3 pt-2">
        {PRICING_FAQS.map((faq, idx) => {
          const isOpen = openIndex === idx;

          return (
            <div
              key={faq.question}
              className="rounded-ds-xl border border-slate-200/80 dark:border-slate-800 bg-white/60 dark:bg-slate-900/60 overflow-hidden transition-all"
            >
              <button
                type="button"
                onClick={() => toggleIndex(idx)}
                className="w-full flex items-center justify-between p-4 focus-ring text-left font-bold text-xs sm:text-sm text-slate-900 dark:text-white"
              >
                <span>{faq.question}</span>
                <ChevronDown
                  className={`w-4 h-4 text-slate-400 transition-transform duration-300 shrink-0 ${
                    isOpen ? 'rotate-180 text-indigo-400' : ''
                  }`}
                />
              </button>

              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="px-4 pb-4 pt-1 text-xs text-slate-600 dark:text-slate-300 leading-relaxed border-t border-slate-200/60 dark:border-slate-800/60">
                      {faq.answer}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </div>
  );
};
