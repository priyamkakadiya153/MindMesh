import React from 'react';
import { BarChart3 } from 'lucide-react';

interface ChartWidgetProps {
  title: string;
  data: Array<{ label: string; value: number; color?: string }>;
}

export function ChartWidget({ title, data }: ChartWidgetProps) {
  const maxVal = Math.max(...data.map(d => d.value), 1);

  return (
    <div className="glass-panel p-5 bg-bgCard border border-borderColor h-full">
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-borderMuted">
        <h3 className="text-sm font-semibold text-textPrimary tracking-wide flex items-center gap-2">
          <BarChart3 size={16} className="text-accentText" />
          <span>{title}</span>
        </h3>
      </div>

      <div className="space-y-3.5 mt-2">
        {data.map((item, i) => {
          const percentage = (item.value / maxVal) * 100;
          return (
            <div key={i} className="space-y-1">
              <div className="flex justify-between text-xs font-medium">
                <span className="text-textSecondary">{item.label}</span>
                <span className="text-textMuted font-semibold">{item.value} files</span>
              </div>
              <div className="w-full bg-bgTertiary rounded-full h-1.5 overflow-hidden border border-borderMuted">
                <div 
                  className="h-full rounded-full bg-accent transition-all duration-500"
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
