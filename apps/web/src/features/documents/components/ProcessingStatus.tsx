import React, { useState, useEffect } from 'react';
import { Document, DocumentAuditLog } from '../types';
import * as api from '../api';

interface ProcessingStatusProps {
  doc: Document;
  token: string;
  orgId: string;
}

interface EventItem {
  id: string;
  stage: string;
  duration_ms: number;
  status: string;
  error?: string;
  timestamp: string;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  doc,
  token,
  orgId
}) => {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await api.getDocumentProcessingStatus(token, orgId, doc.id);
        setEvents(Array.isArray(data) ? data : (data.events || []));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [doc.id, token, orgId]);

  if (loading) {
    return <div className="text-white/40 text-xs animate-pulse p-4">Loading pipeline logs...</div>;
  }

  return (
    <div className="p-5 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl space-y-4">
      <h3 className="text-sm font-bold text-white mb-2 font-outfit">Processing Orchestrator Status</h3>
      
      {events.length === 0 ? (
        <p className="text-xs text-white/40">No ingestion events registered for this document.</p>
      ) : (
        <div className="space-y-3">
          {events.map((event) => (
            <div key={event.id} className="flex justify-between items-center p-3 rounded-xl bg-white/5 border border-white/10 text-xs">
              <div>
                <span className="font-bold text-white/95">{event.stage}</span>
                <span className="block text-[10px] text-white/40">{new Date(event.timestamp).toLocaleTimeString()}</span>
              </div>
              
              <div className="text-right">
                <span className={`px-2 py-0.5 rounded-full text-[10px] border ${
                  event.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' :
                  event.status === 'FAILED' ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                }`}>
                  {event.status}
                </span>
                <span className="block text-[10px] text-white/40 mt-1">{event.duration_ms}ms</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
export default ProcessingStatus;
