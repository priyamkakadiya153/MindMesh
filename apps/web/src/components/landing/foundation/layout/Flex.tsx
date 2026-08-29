import React from 'react';
import { GapSize } from './Grid';

export interface ResponsiveFlexProps extends React.HTMLAttributes<HTMLDivElement> {
  direction?: 'row' | 'column' | 'row-reverse' | 'column-reverse' | 'col-to-row';
  align?: 'start' | 'center' | 'end' | 'baseline' | 'stretch';
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
  wrap?: boolean;
  gap?: GapSize;
  children: React.ReactNode;
}

const dirMap = {
  row: 'flex-row',
  column: 'flex-col',
  'row-reverse': 'flex-row-reverse',
  'column-reverse': 'flex-col-reverse',
  'col-to-row': 'flex-col sm:flex-row',
};

const alignMap = {
  start: 'items-start',
  center: 'items-center',
  end: 'items-end',
  baseline: 'items-baseline',
  stretch: 'items-stretch',
};

const justifyMap = {
  start: 'justify-start',
  center: 'justify-center',
  end: 'justify-end',
  between: 'justify-between',
  around: 'justify-around',
  evenly: 'justify-evenly',
};

const gapMap: Record<GapSize, string> = {
  none: 'gap-0',
  xs: 'gap-2',
  sm: 'gap-4',
  md: 'gap-6',
  lg: 'gap-8',
  xl: 'gap-12',
  '2xl': 'gap-16',
};

export const ResponsiveFlex: React.FC<ResponsiveFlexProps> = ({
  direction = 'row',
  align = 'center',
  justify = 'start',
  wrap = false,
  gap = 'sm',
  className = '',
  children,
  ...props
}) => {
  return (
    <div
      className={`
        flex
        ${dirMap[direction]}
        ${alignMap[align]}
        ${justifyMap[justify]}
        ${wrap ? 'flex-wrap' : 'flex-nowrap'}
        ${gapMap[gap]}
        ${className}
      `.trim()}
      {...props}
    >
      {children}
    </div>
  );
};
