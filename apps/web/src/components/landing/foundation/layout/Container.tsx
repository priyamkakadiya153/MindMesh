import React from 'react';

export type ContainerMaxWidth = 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';

const maxWidthMap: Record<ContainerMaxWidth, string> = {
  sm: 'max-w-3xl',
  md: 'max-w-5xl',
  lg: 'max-w-6xl',
  xl: 'max-w-7xl',
  '2xl': 'max-w-[1440px]',
  full: 'max-w-full',
};

export interface PageContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  maxWidth?: ContainerMaxWidth;
  children: React.ReactNode;
}

export const PageContainer: React.FC<PageContainerProps> = ({
  maxWidth = '2xl',
  className = '',
  children,
  ...props
}) => {
  return (
    <div
      className={`
        w-full mx-auto px-4 mobile-sm:px-5 mobile-lg:px-6 sm:px-8 lg:px-12
        ${maxWidthMap[maxWidth]}
        ${className}
      `.trim()}
      {...props}
    >
      {children}
    </div>
  );
};

export interface SectionWrapperProps extends React.HTMLAttributes<HTMLElement> {
  id?: string;
  spacing?: 'compact' | 'normal' | 'relaxed';
  bg?: 'base' | 'subtle' | 'surface' | 'transparent';
  children: React.ReactNode;
}

const spacingMap = {
  compact: 'py-16 sm:py-20 lg:py-24',
  normal: 'py-24 sm:py-28 lg:py-32',
  relaxed: 'py-28 sm:py-32 lg:py-36',
};


const bgMap = {
  base: 'bg-[var(--color-bg)]',
  subtle: 'bg-[var(--color-bg-subtle)]',
  surface: 'bg-[var(--color-surface)]',
  transparent: 'bg-transparent',
};

export const SectionWrapper: React.FC<SectionWrapperProps> = ({
  id,
  spacing = 'normal',
  bg = 'transparent',
  className = '',
  children,
  ...props
}) => {
  return (
    <section
      id={id}
      className={`
        relative w-full overflow-hidden
        ${spacingMap[spacing]}
        ${bgMap[bg]}
        ${className}
      `.trim()}
      {...props}
    >
      {children}
    </section>
  );
};
