import React from 'react';

interface BulkToolbarProps {
  selectedCount: number;
  onClear: () => void;
  onDelete: () => void;
}

export const BulkToolbar: React.FC<BulkToolbarProps> = ({ selectedCount, onClear, onDelete }) => {
  if (selectedCount === 0) return null;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-6 px-6 py-4 rounded-2xl border border-borderColor bg-bgDialog backdrop-blur-xl shadow-2xl text-textPrimary">
      <span className="text-xs font-semibold text-textPrimary">{selectedCount} documents selected</span>
      <div className="flex gap-3">
        <button
          onClick={onDelete}
          className="px-3.5 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-xs font-bold transition active:scale-95 text-white shadow-md shadow-red-600/25"
        >
          Delete
        </button>
        <button
          onClick={onClear}
          className="px-3.5 py-1.5 rounded-lg bg-bgTertiary hover:bg-bgHover text-xs font-bold transition text-textMuted hover:text-textPrimary border border-borderMuted"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};
export default BulkToolbar;
