import React from 'react';
import { motion } from 'framer-motion';
import { X } from 'lucide-react';

export interface ChipProps extends React.HTMLAttributes<HTMLButtonElement> {
  label: string;
  selected?: boolean;
  onRemove?: () => void;
  icon?: React.ReactNode;
}

export const Chip: React.FC<ChipProps> = ({
  label,
  selected = false,
  onRemove,
  icon,
  className = '',
  onClick,
  ...props
}) => {
  return (
    <motion.button
      type="button"
      whileTap={{ scale: 0.95 }}
      whileHover={{ y: -1 }}
      onClick={onClick}
      className={`
        inline-flex items-center gap-1.5 px-3 py-1.5
        text-xs font-medium rounded-ds-pill transition-all duration-200 focus-ring
        ${
          selected
            ? 'bg-indigo-600 text-white shadow-ds-soft border border-indigo-500'
            : 'bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700'
        }
        ${className}
      `.trim()}
      {...(props as any)}
    >
      {icon && <span className="inline-flex shrink-0">{icon}</span>}
      <span>{label}</span>
      {onRemove && (
        <span
          role="button"
          tabIndex={0}
          aria-label={`Remove ${label}`}
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.stopPropagation();
              onRemove();
            }
          }}
          className="ml-0.5 inline-flex items-center justify-center p-0.5 rounded-full hover:bg-black/10 dark:hover:bg-white/20 transition-colors"
        >
          <X className="w-3 h-3" />
        </span>
      )}
    </motion.button>
  );
};
