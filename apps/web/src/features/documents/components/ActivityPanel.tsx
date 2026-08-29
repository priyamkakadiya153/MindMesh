import React from 'react';

export const ActivityPanel: React.FC = () => {
  return (
    <div className="p-5 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl">
      <h3 className="text-sm font-bold text-white mb-2 font-outfit">Activity Logs</h3>
      <p className="text-xs text-white/40">Audit trail integration is automatically tracked upon document modifications.</p>
    </div>
  );
};
export default ActivityPanel;
