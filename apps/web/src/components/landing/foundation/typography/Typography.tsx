import React from 'react';

export type HeadingLevel = 'display' | 'h1' | 'h2' | 'h3' | 'h4';

export interface HeadingProps extends React.HTMLAttributes<HTMLHeadingElement> {
  level?: HeadingLevel;
  gradient?: boolean;
  as?: React.ElementType;
  children: React.ReactNode;
}

const levelStyles: Record<HeadingLevel, string> = {
  display: 'font-display font-extrabold tracking-tight text-[length:var(--font-display)] leading-[1.08]',
  h1: 'font-display font-extrabold tracking-tight text-[length:var(--font-h1)] leading-[1.12]',
  h2: 'font-display font-extrabold tracking-tight text-[length:var(--font-h2)] leading-[1.2]',
  h3: 'font-display font-bold tracking-tight text-[length:var(--font-h3)] leading-[1.25]',
  h4: 'font-sans font-bold tracking-tight text-[length:var(--font-h4)] leading-[1.3]',
};

const defaultTag: Record<HeadingLevel, React.ElementType> = {
  display: 'h1',
  h1: 'h1',
  h2: 'h2',
  h3: 'h3',
  h4: 'h4',
};

export const Heading: React.FC<HeadingProps> = ({
  level = 'h2',
  gradient = false,
  as,
  className = '',
  children,
  ...props
}) => {
  const Component = as || defaultTag[level];

  const combinedClasses = `
    ${levelStyles[level]}
    ${gradient ? 'text-gradient' : 'text-slate-900 dark:text-white'}
    ${className}
  `.trim();

  return (
    <Component className={combinedClasses} {...props}>
      {children}
    </Component>
  );
};

export type TextVariant = 'bodyLarge' | 'body' | 'small' | 'caption';

export interface TextProps extends React.HTMLAttributes<HTMLParagraphElement> {
  variant?: TextVariant;
  muted?: boolean;
  inverse?: boolean;
  as?: React.ElementType;
  children: React.ReactNode;
}

const textVariantStyles: Record<TextVariant, string> = {
  bodyLarge: 'text-[length:var(--font-body-lg)] leading-[1.65] font-medium',
  body: 'text-[length:var(--font-body)] leading-[1.6] font-medium',
  small: 'text-[length:var(--font-sm)] leading-[1.5] font-medium',
  caption: 'text-[length:var(--font-caption)] leading-[1.4] font-normal tracking-wide uppercase',
};

export const Text: React.FC<TextProps> = ({
  variant = 'body',
  muted = false,
  inverse = false,
  as: Component = 'p',
  className = '',
  children,
  ...props
}) => {
  const colorClass = inverse
    ? 'text-white'
    : muted
    ? 'text-slate-700 dark:text-slate-300 font-medium'
    : 'text-slate-900 dark:text-slate-100 font-medium';

  const combinedClasses = `
    ${textVariantStyles[variant]}
    ${colorClass}
    ${className}
  `.trim();


  return (
    <Component className={combinedClasses} {...props}>
      {children}
    </Component>
  );
};
