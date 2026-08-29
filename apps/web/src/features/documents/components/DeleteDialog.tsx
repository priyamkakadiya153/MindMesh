import React from 'react';

interface DeleteDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  count: number;
}

export const DeleteDialog: React.FC<DeleteDialogProps> = ({ isOpen, onClose, onConfirm, count }) => {
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-dialog-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-bgOverlay backdrop-blur-sm"
    >
      <div className="w-full max-w-sm p-6 rounded-2xl border border-dangerBorder bg-bgDialog shadow-2xl text-textPrimary">
        <h3 id="delete-dialog-title" className="text-md font-bold font-outfit mb-2 text-dangerText">Confirm Soft Delete</h3>
        <p className="text-xs text-textMuted mb-6">
          Are you sure you want to soft delete {count} selected {count === 1 ? 'document' : 'documents'}? This action can be restored later.
        </p>
        
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-bgTertiary hover:bg-bgHover text-xs font-semibold text-textMuted hover:text-textPrimary transition border border-borderMuted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-500 text-xs font-semibold text-white transition shadow-md shadow-red-600/20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};
export default DeleteDialog;
