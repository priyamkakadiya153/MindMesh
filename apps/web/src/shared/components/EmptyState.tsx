import React from 'react';
import { LucideIcon } from 'lucide-react';

export interface EmptyStateAction {
  label: string;
  onClick?: () => void;
  icon?: LucideIcon;
  href?: string;
  variant?: 'primary' | 'secondary' | 'outline';
}

export interface EmptyStateProps {
  title: string;
  description: React.ReactNode;
  icon?: LucideIcon | React.ReactNode;
  primaryAction?: EmptyStateAction;
  secondaryAction?: EmptyStateAction;
  badge?: string;
  variant?: 'page' | 'card' | 'compact' | 'inline';
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  primaryAction,
  secondaryAction,
  badge,
  variant = 'page',
  className = '',
}) => {
  // Determine icon element
  const renderIcon = () => {
    if (!icon) return null;

    if (typeof icon === 'function' || (typeof icon === 'object' && 'render' in (icon as any))) {
      const IconComponent = icon as LucideIcon;
      return <IconComponent className="w-7 h-7 text-accentText transition-transform duration-300 group-hover:scale-110" aria-hidden="true" />;
    }

    return icon as React.ReactNode;
  };

  const isCompact = variant === 'compact' || variant === 'inline';

  return (
    <div
      role="status"
      aria-live="polite"
      className={`relative group overflow-hidden flex flex-col items-center justify-center text-center select-none transition-all duration-300 ${
        variant === 'page'
          ? 'py-12 px-4 sm:px-8 max-w-xl mx-auto my-4 rounded-3xl border border-borderColor bg-bgCard/60 backdrop-blur-xl shadow-xl shadow-accent/5'
          : variant === 'card'
          ? 'p-6 sm:p-8 rounded-2xl border border-borderColor bg-bgCard backdrop-blur-md shadow-sm'
          : 'p-4 rounded-xl border border-borderMuted bg-bgTertiary/50'
      } ${className}`}
    >
      {/* Decorative Subtle Ambient Background Effects */}
      <div className="absolute -top-16 -left-16 w-32 h-32 bg-accent/10 rounded-full blur-2xl pointer-events-none group-hover:bg-accent/15 transition-all duration-500" aria-hidden="true" />
      <div className="absolute -bottom-16 -right-16 w-32 h-32 bg-accent/5 rounded-full blur-2xl pointer-events-none" aria-hidden="true" />

      {/* Optional Badge / Pill */}
      {badge && (
        <span className="mb-3 px-2.5 py-0.5 text-[10px] font-semibold font-mono tracking-wider uppercase bg-accentSubtle text-accentText border border-accent/30 rounded-full">
          {badge}
        </span>
      )}

      {/* Illustration Badge Container */}
      {icon && (
        <div className="relative mb-4 flex items-center justify-center">
          {/* Concentric Glow Rings */}
          <div className="absolute inset-0 rounded-full bg-accent/20 blur-md animate-pulse" aria-hidden="true" />
          <div className="relative flex h-14 w-14 sm:h-16 sm:w-16 items-center justify-center rounded-2xl bg-gradient-to-b from-bgCard to-bgTertiary border border-borderColor shadow-lg shadow-accent/10 group-hover:border-accent/40 transition-colors">
            {/* Minimal Grid Overlay */}
            <svg
              className="absolute inset-0 h-full w-full opacity-10 text-accentText"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={0.5} d="M4 4h16v16H4zM4 12h16M12 4v16" />
            </svg>
            {renderIcon()}
          </div>
        </div>
      )}

      {/* Content Area */}
      <h3 className={`font-bold text-textPrimary tracking-tight ${isCompact ? 'text-sm mb-1' : 'text-base sm:text-lg mb-1.5'}`}>
        {title}
      </h3>

      <div className={`text-textMuted leading-relaxed ${isCompact ? 'text-[11px] max-w-xs mb-3' : 'text-xs sm:text-sm max-w-md mb-6'}`}>
        {typeof description === 'string' ? <p>{description}</p> : description}
      </div>

      {/* CTA Buttons */}
      {(primaryAction || secondaryAction) && (
        <div className={`flex flex-col sm:flex-row items-center justify-center gap-2.5 w-full ${isCompact ? 'sm:w-auto' : 'sm:w-auto'}`}>
          {primaryAction && (
            <button
              onClick={primaryAction.onClick}
              type="button"
              aria-label={primaryAction.label}
              title={primaryAction.label}
              className="w-full sm:w-auto px-4 py-2 text-xs font-semibold rounded-xl bg-accent hover:bg-accentHover text-white shadow-lg shadow-accent/25 hover:shadow-accent/40 active:scale-95 transition-all flex items-center justify-center gap-2 border border-accent/20 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              {primaryAction.icon && <primaryAction.icon className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />}
              <span>{primaryAction.label}</span>
            </button>
          )}

          {secondaryAction && (
            <button
              onClick={secondaryAction.onClick}
              type="button"
              aria-label={secondaryAction.label}
              title={secondaryAction.label}
              className="w-full sm:w-auto px-4 py-2 text-xs font-medium rounded-xl bg-bgInput hover:bg-bgHover text-textSecondary hover:text-textPrimary border border-borderColor hover:border-accent/40 active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              {secondaryAction.icon && <secondaryAction.icon className="w-3.5 h-3.5 text-textMuted shrink-0" aria-hidden="true" />}
              <span>{secondaryAction.label}</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default EmptyState;
