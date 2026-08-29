import React from 'react';
import { FAQ_CATEGORIES, FAQCategory } from './faq-dataset';

export interface FAQCategoryTabsProps {
  activeCategory: FAQCategory;
  onSelectCategory: (cat: FAQCategory) => void;
}


export const FAQCategoryTabs: React.FC<FAQCategoryTabsProps> = ({
  activeCategory,
  onSelectCategory,
}) => {
  return (
    <div className="flex items-center justify-start sm:justify-center gap-1.5 overflow-x-auto no-scrollbar py-1">
      {FAQ_CATEGORIES.map((cat) => (
        <button
          key={cat.id}
          type="button"
          onClick={() => onSelectCategory(cat.id)}
          className={`text-xs sm:text-sm px-4 py-2 rounded-ds-pill font-bold transition-all border shrink-0 min-h-[44px] flex items-center ${
            activeCategory === cat.id
              ? 'bg-indigo-600 text-white border-indigo-500 shadow-ds-soft'
              : 'bg-white dark:bg-slate-900/80 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-800 hover:text-slate-900 dark:hover:text-white'
          }`}

        >
          {cat.label}
        </button>

      ))}
    </div>
  );
};
