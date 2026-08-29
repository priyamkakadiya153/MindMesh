import React from 'react';
import { RelatedItem } from '../connections-api';
import { Brain, CheckSquare, MessageSquare, FileText, User, ArrowRight } from 'lucide-react';

interface GroupedConnectedEntitiesProps {
  grouped: Record<string, RelatedItem[]>;
  onSelectEntity: (type: string, id: string) => void;
}

export const GroupedConnectedEntities: React.FC<GroupedConnectedEntitiesProps> = ({
  grouped,
  onSelectEntity
}) => {
  const categories = [
    { key: 'DECISIONS', label: 'DECISIONS', icon: <Brain className="w-4 h-4 text-amber-400" /> },
    { key: 'TASKS', label: 'TASKS', icon: <CheckSquare className="w-4 h-4 text-emerald-400" /> },
    { key: 'CONVERSATIONS', label: 'CONVERSATIONS', icon: <MessageSquare className="w-4 h-4 text-purple-400" /> },
    { key: 'DOCUMENTS', label: 'DOCUMENTS', icon: <FileText className="w-4 h-4 text-blue-400" /> },
    { key: 'PEOPLE', label: 'PEOPLE & USERS', icon: <User className="w-4 h-4 text-pink-400" /> }
  ];

  const hasAnyGroupedItems = Object.values(grouped || {}).some(list => list && list.length > 0);

  if (!hasAnyGroupedItems) {
    return (
      <div className="p-6 bg-slate-900/40 border border-slate-800 rounded-3xl text-center space-y-2">
        <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">CONNECTED WORKSPACE ENTITIES</span>
        <p className="text-xs text-slate-500">No connected decisions, tasks, conversations, or documents found for this item yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/70 border border-slate-800 rounded-3xl p-5 md:p-6 space-y-5 shadow-xl select-none">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
            RELATIONSHIP MAP
          </span>
          <h3 className="text-base font-bold text-white">Connected Entities</h3>
        </div>
        <span className="text-xs text-slate-400">Grouped by relationship type</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {categories.map((cat) => {
          const items = grouped[cat.key] || [];
          if (items.length === 0) return null;

          return (
            <div key={cat.key} className="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-4 space-y-3">
              <div className="flex items-center space-x-2 pb-2 border-b border-slate-800/60">
                {cat.icon}
                <span className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider">
                  {cat.label} ({items.length})
                </span>
              </div>

              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {items.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => onSelectEntity(item.type, item.id)}
                    className="p-2.5 bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 rounded-xl cursor-pointer transition-all flex items-center justify-between group"
                  >
                    <div className="min-w-0 pr-2 space-y-0.5">
                      <span className="text-xs font-medium text-slate-200 block truncate group-hover:text-indigo-300 transition-colors">
                        {item.title}
                      </span>
                      <span className="text-[10px] text-indigo-400 font-mono block">
                        {item.relation}
                      </span>
                    </div>

                    <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-all shrink-0" />
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
