import React from 'react';

export type GapSize = 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';

const gapMap: Record<GapSize, string> = {
  none: 'gap-0',
  xs: 'gap-2 mobile-sm:gap-3',
  sm: 'gap-4 mobile-sm:gap-5',
  md: 'gap-6 mobile-sm:gap-7 sm:gap-8',
  lg: 'gap-8 mobile-sm:gap-9 sm:gap-10 lg:gap-12',
  xl: 'gap-10 sm:gap-12 lg:gap-16',
  '2xl': 'gap-12 sm:gap-16 lg:gap-20',
};

export interface ResponsiveGridProps extends React.HTMLAttributes<HTMLDivElement> {
  cols?: {
    base?: number;
    mobileSm?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  gap?: GapSize;
  children: React.ReactNode;
}

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  cols = { base: 1, sm: 2, lg: 3 },
  gap = 'md',
  className = '',
  children,
  ...props
}) => {
  const colClasses = [
    cols.base ? `grid-cols-${cols.base}` : 'grid-cols-1',
    cols.mobileSm ? `mobile-sm:grid-cols-${cols.mobileSm}` : '',
    cols.sm ? `sm:grid-cols-${cols.sm}` : '',
    cols.md ? `md:grid-cols-${cols.md}` : '',
    cols.lg ? `lg:grid-cols-${cols.lg}` : '',
    cols.xl ? `xl:grid-cols-${cols.xl}` : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      className={`
        grid w-full
        ${colClasses}
        ${gapMap[gap]}
        ${className}
      `.trim()}
      {...props}
    >
      {children}
    </div>
  );
};

export interface FluidGridProps extends React.HTMLAttributes<HTMLDivElement> {
  minWidth?: number; // e.g. 280
  gap?: GapSize;
  children: React.ReactNode;
}

export const FluidGrid: React.FC<FluidGridProps> = ({
  minWidth = 280,
  gap = 'md',
  className = '',
  children,
  ...props
}) => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(auto-fill, minmax(min(100%, ${minWidth}px), 1fr))`,
      }}
      className={`
        w-full
        ${gapMap[gap]}
        ${className}
      `.trim()}
      {...props}
    >
      {children}
    </div>
  );
};
