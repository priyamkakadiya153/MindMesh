import React from 'react';

export const TagManager: React.FC = () => {
  return (
    <div className="p-4 rounded-xl border border-white/5 bg-white/5">
      <h4 className="text-xs font-bold text-white mb-2">Labels Manager</h4>
      <div className="flex flex-wrap gap-2 text-xs text-white/60">
        <span className="px-2 py-1 rounded bg-indigo-500/10 border border-indigo-500/20">Engineering</span>
        <span className="px-2 py-1 rounded bg-indigo-500/10 border border-indigo-500/20">Policy</span>
      </div>
    </div>
  );
};
export default TagManager;
