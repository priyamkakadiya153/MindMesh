import React from 'react';
import { useDocumentsStore } from '../store';
import { X, CheckCircle, AlertTriangle, Loader2, ArrowUpRight } from 'lucide-react';

export const UploadProgress: React.FC = () => {
  const { uploadQueue, removeUploadQueueItem, clearUploadQueue } = useDocumentsStore();

  if (uploadQueue.length === 0) return null;

  const activeUploads = uploadQueue.filter(item => item.status === 'uploading' || item.status === 'queued' || item.status === 'processing');

  return (
    <div className="fixed bottom-6 right-6 z-50 w-96 max-w-[90vw] rounded-2xl border border-borderColor bg-bgDialog backdrop-blur-2xl p-4 shadow-2xl font-outfit text-textPrimary space-y-3 animate-in fade-in slide-in-from-bottom-5">
      <div className="flex items-center justify-between border-b border-borderMuted pb-2.5">
        <div className="flex items-center gap-2">
          {activeUploads.length > 0 ? (
            <Loader2 className="w-4 h-4 text-accentText animate-spin" />
          ) : (
            <CheckCircle className="w-4 h-4 text-successText" />
          )}
          <span className="text-xs font-bold tracking-tight">
            {activeUploads.length > 0 ? `Uploading (${activeUploads.length} active)` : 'Uploads Completed'}
          </span>
        </div>
        <button
          onClick={clearUploadQueue}
          className="text-textMuted hover:text-textPrimary text-xs px-2 py-0.5 rounded-lg hover:bg-bgHover transition-colors"
        >
          Clear
        </button>
      </div>

      <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
        {uploadQueue.map((item) => (
          <div key={item.id} className="bg-bgTertiary border border-borderMuted p-3 rounded-xl space-y-2 text-xs">
            <div className="flex items-center justify-between gap-2">
              <span className="font-semibold truncate text-textPrimary max-w-[180px]">{item.name}</span>
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                  item.status === 'completed' ? 'bg-successBg text-successText border border-successBorder' :
                  item.status === 'failed' ? 'bg-dangerBg text-dangerText border border-dangerBorder' :
                  'bg-accentSubtle text-accentText border border-accent/30'
                }`}>
                  {item.status}
                </span>
                <button
                  onClick={() => removeUploadQueueItem(item.id)}
                  className="text-textMuted hover:text-textPrimary transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {item.status === 'uploading' && (
              <div className="space-y-1">
                <div className="w-full h-1.5 bg-bgInput rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent transition-all duration-300 rounded-full"
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-textMuted">
                  <span>{item.progress}%</span>
                  <span>{item.speed || '2.4 MB/s'} • {item.remainingTime || '3s left'}</span>
                </div>
              </div>
            )}

            {item.status === 'failed' && (
              <p className="text-[10px] text-dangerText font-medium">{item.error || 'Upload interrupted or rejected by server.'}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default UploadProgress;

