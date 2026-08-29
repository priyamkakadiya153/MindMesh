import React from 'react';
import { useDocumentsStore } from '../store';
import { RefreshCw, X, Trash2, CheckCircle2, AlertCircle } from 'lucide-react';

interface UploadQueueProps {
  onRetry?: (id: string) => void;
  onCancel?: (id: string) => void;
}

export const UploadQueue: React.FC<UploadQueueProps> = ({ onRetry, onCancel }) => {
  const { uploadQueue, clearCompletedQueue, clearFailedQueue, clearUploadQueue, removeUploadQueueItem } = useDocumentsStore();

  if (uploadQueue.length === 0) return null;

  const completedCount = uploadQueue.filter(i => i.status === 'completed').length;
  const failedCount = uploadQueue.filter(i => i.status === 'failed' || i.status === 'cancelled').length;

  return (
    <div className="w-full bg-bgCard border border-borderColor p-4 rounded-2xl backdrop-blur-xl space-y-3 font-outfit">
      <div className="flex justify-between items-center pb-2 border-b border-borderMuted">
        <h4 className="text-xs font-bold text-textPrimary tracking-tight">Upload Queue ({uploadQueue.length})</h4>
        <div className="flex items-center gap-2 text-[11px]">
          {completedCount > 0 && (
            <button
              onClick={clearCompletedQueue}
              className="text-textMuted hover:text-successText transition font-medium"
            >
              Clear Completed ({completedCount})
            </button>
          )}
          {failedCount > 0 && (
            <button
              onClick={clearFailedQueue}
              className="text-textMuted hover:text-dangerText transition font-medium"
            >
              Clear Failed ({failedCount})
            </button>
          )}
          <button
            onClick={clearUploadQueue}
            className="text-textMuted hover:text-textPrimary transition"
          >
            Clear All
          </button>
        </div>
      </div>

      <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
        {uploadQueue.map((item) => (
          <div key={item.id} className="flex flex-col space-y-1 bg-bgTertiary p-2.5 rounded-xl border border-borderMuted text-xs">
            <div className="flex justify-between items-center">
              <span className="text-textPrimary font-medium truncate max-w-[180px]" title={item.name}>
                {item.name}
              </span>
              <div className="flex items-center gap-1.5">
                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                  item.status === 'completed' ? 'bg-successBg text-successText border border-successBorder' :
                  item.status === 'failed' ? 'bg-dangerBg text-dangerText border border-dangerBorder' :
                  item.status === 'cancelled' ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20' :
                  'bg-accentSubtle text-accentText border border-accent/30'
                }`}>
                  {item.status}
                </span>

                {(item.status === 'failed' || item.status === 'cancelled') && onRetry && (
                  <button
                    onClick={() => onRetry(item.id)}
                    className="p-1 rounded-lg hover:bg-bgHover text-accentText transition-all"
                    title="Retry upload"
                  >
                    <RefreshCw size={12} />
                  </button>
                )}

                {(item.status === 'uploading' || item.status === 'queued') && onCancel && (
                  <button
                    onClick={() => onCancel(item.id)}
                    className="p-1 rounded-lg hover:bg-bgHover text-dangerText transition-all"
                    title="Cancel upload"
                  >
                    <X size={12} />
                  </button>
                )}

                <button
                  onClick={() => removeUploadQueueItem(item.id)}
                  className="p-1 rounded-lg hover:bg-bgHover text-textMuted hover:text-textPrimary transition-all"
                  title="Remove from queue"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            </div>
            
            {item.status === 'uploading' && (
              <div className="w-full bg-bgInput h-1.5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent transition-all duration-300 rounded-full"
                  style={{ width: `${item.progress}%` }}
                />
              </div>
            )}

            {item.error && (
              <span className="text-[10px] text-dangerText truncate w-full font-medium">
                {item.error}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
export default UploadQueue;
