import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'outline';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  children: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-indigo-600 hover:bg-indigo-500 text-white shadow-ds-medium hover:shadow-ds-hero border border-indigo-500/30 dark:bg-indigo-600 dark:hover:bg-indigo-500',
  secondary:
    'bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 shadow-ds-soft border border-slate-700/20 dark:border-slate-200/20',
  ghost:
    'bg-transparent hover:bg-slate-500/10 text-slate-700 dark:text-slate-200 hover:text-indigo-600 dark:hover:text-indigo-400 border border-transparent',
  outline:
    'bg-transparent hover:bg-indigo-500/10 text-slate-800 dark:text-slate-100 border border-slate-300 dark:border-slate-700 hover:border-indigo-500 dark:hover:border-indigo-400',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-xs font-medium rounded-ds-md gap-1.5 min-h-[34px]',
  md: 'px-4 py-2.5 text-sm font-semibold rounded-ds-md gap-2 min-h-[42px]',
  lg: 'px-6 py-3.5 text-base font-semibold rounded-ds-lg gap-2.5 min-h-[50px]',
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  disabled,
  className = '',
  children,
  onClick,
  type = 'button',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();

  const baseClasses = `
    inline-flex items-center justify-center
    transition-all duration-200 ease-in-out
    select-none focus-ring disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
    ${variantStyles[variant]}
    ${sizeStyles[size]}
    ${fullWidth ? 'w-full' : ''}
    ${className}
  `.trim();

  return (
    <motion.button
      type={type}
      disabled={disabled || isLoading}
      onClick={onClick}
      whileTap={shouldReduceMotion || disabled || isLoading ? undefined : { scale: 0.97 }}
      whileHover={shouldReduceMotion || disabled || isLoading ? undefined : { y: -1 }}
      className={baseClasses}
      {...(props as any)}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current mr-1" aria-hidden="true" />
      ) : leftIcon ? (
        <span className="inline-flex shrink-0 items-center">{leftIcon}</span>
      ) : null}

      <span>{children}</span>

      {!isLoading && rightIcon && (
        <span className="inline-flex shrink-0 items-center">{rightIcon}</span>
      )}
    </motion.button>
  );
};
