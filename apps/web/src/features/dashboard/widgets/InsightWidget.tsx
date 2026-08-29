import React from 'react';
import { Bot, Lightbulb } from 'lucide-react';

interface InsightWidgetProps {
  insights: string;
}

export function InsightWidget({ insights }: InsightWidgetProps) {
  return (
    <div className="glass-panel p-5 bg-accentSubtle border border-accent/20 h-full flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-accent/20">
          <h3 className="text-sm font-semibold text-accentText tracking-wide flex items-center gap-2">
            <Bot size={16} className="text-accentText" />
            <span>AI Knowledge Insights</span>
          </h3>
        </div>

        <div className="p-3 bg-bgCard border border-borderColor rounded-xl">
          <div className="flex gap-2.5 items-start text-xs">
            <Lightbulb size={16} className="text-amber-500 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-textPrimary">Personalized Briefing</p>
              <p className="text-textSecondary mt-1 leading-relaxed text-[11px]">{insights}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
