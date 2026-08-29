import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatisticWidgetProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  changeText?: string;
  changeType?: 'up' | 'down' | 'neutral';
  color?: string;
}

export function StatisticWidget({
  title,
  value,
  icon: Icon,
  changeText,
  changeType = 'neutral',
  color = 'indigo'
}: StatisticWidgetProps) {
  return (
    <div className="glass-panel p-5 bg-bgCard hover:bg-bgCardHover border border-borderColor hover:border-accent/20 transition-all duration-300 flex flex-col justify-between group">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-textMuted uppercase tracking-widest font-semibold">{title}</p>
          <h3 className="text-3xl font-extrabold text-textPrimary mt-2 leading-none">{value}</h3>
        </div>
        <div className="p-2 rounded-xl bg-accentSubtle text-accentText group-hover:scale-110 transition-all duration-300">
          <Icon size={18} />
        </div>
      </div>
      
      {changeText && (
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-borderMuted text-[10px]">
          <span className="text-textMuted">{changeText}</span>
          <span className={`font-semibold uppercase tracking-wider ${
            changeType === 'up' ? 'text-successText' : changeType === 'down' ? 'text-dangerText' : 'text-accentText'
          }`}>
            {changeType === 'up' ? 'Active' : changeType === 'down' ? 'Alert' : 'Pending'}
          </span>
        </div>
      )}
    </div>
  );
}
