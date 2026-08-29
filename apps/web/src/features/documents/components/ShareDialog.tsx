import React from 'react';

interface ShareDialogProps {
  isOpen: boolean;
  onClose: () => void;
  filename: string;
}

export const ShareDialog: React.FC<ShareDialogProps> = ({ isOpen, onClose, filename }) => {
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
      aria-labelledby="share-dialog-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-bgOverlay backdrop-blur-sm"
    >
      <div className="w-full max-w-md p-6 rounded-2xl border border-borderColor bg-bgDialog shadow-2xl text-textPrimary">
        <h3 id="share-dialog-title" className="text-md font-bold font-outfit mb-2 text-textPrimary">Share Knowledge Asset</h3>
        <p className="text-xs text-textMuted mb-4">Provide access permissions for "{filename}" to organization members.</p>
        
        <div className="space-y-4">
          <label htmlFor="share-email-input" className="sr-only">Search email address</label>
          <input
            id="share-email-input"
            type="email"
            placeholder="Search email address..."
            aria-label="Search email address"
            className="w-full bg-bgInput border border-borderColor rounded-xl px-3 py-2 text-xs text-textPrimary focus:outline-none focus:border-accent focus-visible:ring-2 focus-visible:ring-accent transition"
          />
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-bgTertiary hover:bg-bgHover text-xs font-semibold text-textMuted hover:text-textPrimary border border-borderMuted transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => { alert('Access permission link copied to clipboard.'); onClose(); }}
              className="px-4 py-2 rounded-xl bg-accent hover:bg-accentHover text-xs font-semibold text-white transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              Copy Link
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
export default ShareDialog;
