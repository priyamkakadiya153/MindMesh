import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { IconButton } from '../buttons/IconButton';

// --- DIVIDER ---
export interface DividerProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: 'horizontal' | 'vertical';
  gradient?: boolean;
  label?: string;
}

export const Divider: React.FC<DividerProps> = ({
  orientation = 'horizontal',
  gradient = false,
  label,
  className = '',
  ...props
}) => {
  if (orientation === 'vertical') {
    return (
      <div
        className={`
          inline-block self-stretch w-px
          ${gradient ? 'bg-gradient-to-b from-transparent via-slate-300 dark:via-slate-700 to-transparent' : 'bg-slate-200 dark:bg-slate-800'}
          ${className}
        `.trim()}
        {...props}
      />
    );
  }

  if (label) {
    return (
      <div className={`relative flex items-center w-full my-4 ${className}`} {...props}>
        <div className="flex-grow border-t border-slate-200 dark:border-slate-800" />
        <span className="shrink-0 px-3 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {label}
        </span>
        <div className="flex-grow border-t border-slate-200 dark:border-slate-800" />
      </div>
    );
  }

  return (
    <hr
      className={`
        w-full border-0 h-px my-4
        ${gradient ? 'bg-gradient-to-r from-transparent via-slate-300 dark:via-slate-700 to-transparent' : 'bg-slate-200 dark:bg-slate-800'}
        ${className}
      `.trim()}
      {...props}
    />
  );
};

// --- TOOLTIP ---
export interface TooltipProps {
  content: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
  children: React.ReactNode;
}

const positionClasses = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
};

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  position = 'top',
  children,
}) => {
  const [isVisible, setIsVisible] = React.useState(false);

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
    >
      {children}
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: position === 'top' ? 4 : position === 'bottom' ? -4 : 0 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.15 }}
            role="tooltip"
            className={`
              absolute z-50 pointer-events-none px-2.5 py-1 text-xs font-medium
              text-white bg-slate-900 dark:bg-slate-100 dark:text-slate-900 rounded-ds-sm
              shadow-ds-floating whitespace-nowrap
              ${positionClasses[position]}
            `.trim()}
          >
            {content}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// --- MODAL CONTAINER ---
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl';
}

const modalMaxWidthMap = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
};

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  maxWidth = 'md',
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Lock scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm"
          />

          {/* Modal Container */}
          <motion.div
            ref={modalRef}
            initial={{ opacity: 0, scale: 0.95, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 12 }}
            transition={{ duration: 0.25, ease: [0.19, 1, 0.22, 1] }}
            role="dialog"
            aria-modal="true"
            aria-labelledby={title ? 'modal-title' : undefined}
            className={`
              relative w-full z-10 p-6 sm:p-8 rounded-ds-2xl
              bg-slate-900/90 dark:bg-slate-900/95 border border-slate-800
              shadow-ds-modal text-white overflow-hidden
              ${modalMaxWidthMap[maxWidth]}
            `.trim()}
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                {title && (
                  <h3 id="modal-title" className="text-xl font-bold text-slate-900 dark:text-white">
                    {title}
                  </h3>
                )}
                {description && (
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    {description}
                  </p>
                )}
              </div>
              <IconButton
                icon={<X className="w-5 h-5" />}
                aria-label="Close modal"
                variant="ghost"
                onClick={onClose}
              />
            </div>

            {/* Content */}
            <div className="relative">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
