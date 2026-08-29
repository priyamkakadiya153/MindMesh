import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { ButtonVariant, ButtonSize } from './Button';

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  icon: React.ReactNode;
  'aria-label': string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  rounded?: boolean;
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-12 h-12 text-base',
};

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-ds-soft',
  secondary: 'bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900',
  ghost: 'bg-transparent hover:bg-slate-500/10 text-slate-600 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400',
  outline: 'bg-transparent border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:border-indigo-500',
};

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  'aria-label': ariaLabel,
  variant = 'ghost',
  size = 'md',
  rounded = false,
  className = '',
  disabled,
  onClick,
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.button
      type="button"
      aria-label={ariaLabel}
      disabled={disabled}
      onClick={onClick}
      whileTap={shouldReduceMotion || disabled ? undefined : { scale: 0.92 }}
      whileHover={shouldReduceMotion || disabled ? undefined : { scale: 1.05 }}
      className={`
        inline-flex items-center justify-center shrink-0
        transition-all duration-200 ease-in-out focus-ring
        ${sizeStyles[size]}
        ${variantStyles[variant]}
        ${rounded ? 'rounded-full' : 'rounded-ds-md'}
        ${className}
      `.trim()}
      {...(props as any)}
    >
      {icon}
    </motion.button>
  );
};
