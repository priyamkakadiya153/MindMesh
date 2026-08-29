import React, { useState, useEffect } from 'react';
import { Document, DocumentVersion } from '../types';
import * as api from '../api';

interface VersionHistoryProps {
  doc: Document;
  token: string;
  orgId: string;
  onRestoreSuccess?: () => void;
}

export const VersionHistory: React.FC<VersionHistoryProps> = ({
  doc,
  token,
  orgId,
  onRestoreSuccess
}) => {
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [loading, setLoading] = useState(true);

  const loadVersions = async () => {
    try {
      setLoading(true);
      const data = await api.getDocumentVersions(token, orgId, doc.id);
      setVersions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVersions();
  }, [doc.id, token, orgId]);

  const handleRestore = async (versionNumber: number) => {
    if (!confirm(`Are you sure you want to restore to version ${versionNumber}?`)) return;
    try {
      await api.restoreDocumentVersion(token, orgId, doc.id, versionNumber);
      loadVersions();
      if (onRestoreSuccess) onRestoreSuccess();
    } catch (err) {
      alert("Failed to restore version: " + err);
    }
  };

  if (loading) {
    return <div className="text-textMuted text-xs animate-pulse p-4">Loading version timeline...</div>;
  }

  return (
    <div className="p-5 rounded-2xl border border-borderColor bg-bgCard backdrop-blur-xl space-y-4">
      <h3 className="text-sm font-bold text-textPrimary mb-2 font-outfit">Version History</h3>
      
      {versions.length === 0 ? (
        <p className="text-xs text-textMuted">Only initial version v{doc.version} is currently uploaded.</p>
      ) : (
        <div className="relative border-l border-borderMuted ml-2 pl-4 space-y-5">
          {versions.map((ver) => (
            <div key={ver.id} className="relative group">
              <div className="absolute -left-[21px] top-1.5 h-3.5 w-3.5 rounded-full bg-accent border-2 border-bgCard group-hover:bg-accentHover transition" />
              <div className="flex justify-between items-start gap-4">
                <div>
                  <h4 className="text-xs font-semibold text-textPrimary">
                    Version {ver.version_number}
                  </h4>
                  <p className="text-[10px] text-textMuted">
                    {new Date(ver.created_at).toLocaleString()}
                  </p>
                  {ver.change_summary && (
                    <p className="text-[11px] text-textSecondary mt-1 italic">
                      "{ver.change_summary}"
                    </p>
                  )}
                </div>

                {ver.version_number !== doc.version && (
                  <button
                    onClick={() => handleRestore(ver.version_number)}
                    className="px-2 py-1 rounded bg-accentSubtle hover:bg-accent text-[10px] font-semibold text-accentText hover:text-white transition border border-accent/20"
                  >
                    Restore
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
export default VersionHistory;
