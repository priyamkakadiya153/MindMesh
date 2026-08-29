import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

export type CardElevation = 'none' | 'soft' | 'medium' | 'floating' | 'hero';
export type CardPadding = 'none' | 'sm' | 'md' | 'lg';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevation?: CardElevation;
  padding?: CardPadding;
  hoverLift?: boolean;
  glowOnHover?: boolean;
  bordered?: boolean;
  variant?: 'default' | 'interactive' | 'flat' | string;
  children: React.ReactNode;
}

const elevationMap: Record<CardElevation, string> = {
  none: '',
  soft: 'shadow-ds-soft',
  medium: 'shadow-ds-medium',
  floating: 'shadow-ds-floating',
  hero: 'shadow-ds-hero',
};

const paddingMap: Record<CardPadding, string> = {
  none: 'p-0',
  sm: 'p-4 mobile-sm:p-5',
  md: 'p-6 mobile-sm:p-7 sm:p-8',
  lg: 'p-8 mobile-sm:p-9 sm:p-10 lg:p-12',
};

export const Card: React.FC<CardProps> = ({
  elevation = 'soft',
  padding = 'md',
  hoverLift = true,
  glowOnHover = false,
  bordered = true,
  variant,
  className = '',
  children,
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  const isInteractive = variant === 'interactive';
  const effectiveGlow = glowOnHover || isInteractive;

  const hasBgClass = className.split(' ').some((cls) => cls.startsWith('bg-') || cls.includes(':bg-'));
  const defaultBg = hasBgClass ? '' : 'bg-white/80 dark:bg-slate-900/80';

  const combinedClasses = `
    relative rounded-ds-xl transition-all duration-300 ease-out backdrop-blur-md
    ${defaultBg}
    ${bordered ? 'border border-slate-200/80 dark:border-slate-800/80' : ''}
    ${elevationMap[elevation]}
    ${paddingMap[padding]}
    ${effectiveGlow ? 'hover:border-indigo-500/50 hover:shadow-ds-glow' : ''}
    ${className}
  `.trim();

  if (hoverLift && !shouldReduceMotion) {
    return (
      <motion.div
        whileHover={{ y: -6, transition: { duration: 0.25, ease: [0.19, 1, 0.22, 1] } }}
        className={combinedClasses}
        {...(props as any)}
      >
        {children}
      </motion.div>
    );
  }

  return (
    <div className={combinedClasses} {...props}>
      {children}
    </div>
  );
};

export interface GlassContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  intensity?: 'light' | 'medium' | 'heavy';
  padding?: CardPadding;
  glow?: boolean;
  children: React.ReactNode;
}

const intensityMap = {
  light: 'bg-white/40 dark:bg-slate-900/40 backdrop-blur-sm border-white/20 dark:border-slate-800/50',
  medium: 'bg-white/70 dark:bg-slate-900/70 backdrop-blur-md border-white/30 dark:border-slate-700/50',
  heavy: 'bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl border-white/40 dark:border-slate-600/50',
};

export const GlassContainer: React.FC<GlassContainerProps> = ({
  intensity = 'medium',
  padding = 'md',
  glow = false,
  className = '',
  children,
  ...props
}) => {
  return (
    <div
      className={`
        relative rounded-ds-xl border shadow-ds-medium transition-all duration-300
        ${intensityMap[intensity]}
        ${paddingMap[padding]}
        ${glow ? 'shadow-ds-glow border-indigo-500/40' : ''}
        ${className}
      `.trim()}
      {...props}
    >
      {children}
    </div>
  );
};
