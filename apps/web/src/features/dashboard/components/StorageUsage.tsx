import React from 'react';
import { Database, HardDrive } from 'lucide-react';

interface StorageUsageProps {
  usedBytes: number;
  maxBytes?: number;
}

export function StorageUsage({ usedBytes, maxBytes = 10737418240 }: StorageUsageProps) { // default 10GB
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const dm = 1;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  const percentage = Math.min((usedBytes / maxBytes) * 100, 100);

  return (
    <div className="glass-panel p-3.5 bg-bgCard border border-borderColor h-full flex flex-col justify-between rounded-2xl">
      <div>
        <div className="flex items-center justify-between mb-2.5 pb-1.5 border-b border-borderMuted">
          <h2 className="text-xs font-semibold text-textPrimary tracking-wide flex items-center gap-2">
            <HardDrive size={15} className="text-accentText" aria-hidden="true" />
            <span>Storage Usage</span>
          </h2>
          <span className="text-[9px] text-textMuted font-medium">Capacities</span>
        </div>

        <div className="space-y-2.5">
          <div className="flex justify-between items-end">
            <div>
              <div className="text-xl font-bold text-textPrimary">{formatBytes(usedBytes)}</div>
              <div className="text-[9px] text-textMuted font-medium mt-0.5">Used of {formatBytes(maxBytes)}</div>
            </div>
            <div className="p-1.5 rounded-lg bg-accentSubtle text-accentText" aria-hidden="true">
              <Database size={15} />
            </div>
          </div>

          <div className="space-y-1">
            <div 
              role="progressbar"
              aria-valuenow={Math.round(percentage)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Storage usage: ${percentage.toFixed(1)}% used`}
              className="w-full bg-bgTertiary rounded-full h-1.5 overflow-hidden border border-borderMuted"
            >
              <div 
                className="bg-accent h-full rounded-full transition-all duration-500" 
                style={{ width: `${percentage}%` }}
              />
            </div>
            <div className="flex justify-between text-[9px] text-textMuted font-semibold">
              <span>{percentage.toFixed(1)}% Used</span>
              <span>{formatBytes(maxBytes - usedBytes)} Free</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-2.5 pt-2 border-t border-borderMuted text-[9px] text-textMuted leading-relaxed">
        Storage logs sync with uploaded document size metadata. Vector databases are hosted externally.
      </div>
    </div>
  );
}
