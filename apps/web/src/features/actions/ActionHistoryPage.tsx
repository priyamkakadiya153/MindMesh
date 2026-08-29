import React, { useState, useEffect } from 'react';
import { History, CheckCircle2, XCircle, Clock, AlertTriangle, Filter, Calendar, User, MessageSquare, Bot, Layers } from 'lucide-react';
import { apiClient } from '../../lib/api-client';

interface ActionEventItem {
  id: string;
  action_type: string;
  status: string;
  source_type: string;
  target_type: string;
  target_id: string | null;
  before_state: any;
  after_state: any;
  reason: string | null;
  created_at: string;
}

export const ActionHistoryPage: React.FC = () => {
  const [events, setEvents] = useState<ActionEventItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [days, setDays] = useState<number>(7);
  const [selectedSource, setSelectedSource] = useState<string>('ALL');

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const params: any = { days };
      if (selectedSource !== 'ALL') {
        params.source_type = selectedSource;
      }
      const res = await apiClient.get('/actions/history', { params });
      setEvents(res.data.events || []);
    } catch (err) {
      console.error('Failed to fetch action history', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [days, selectedSource]);

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case 'SUCCEEDED':
      case 'SUCCESS':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" /> Succeeded
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
            <XCircle className="w-3 h-3" /> Failed
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3 h-3" /> Cancelled
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20">
            <Clock className="w-3 h-3" /> {status}
          </span>
        );
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-borderColor pb-5">
        <div>
          <h1 className="text-2xl font-bold text-textColor flex items-center gap-2.5">
            <History className="w-7 h-7 text-accent" /> Action Memory & Audit Trail
          </h1>
          <p className="text-sm text-subTextColor mt-1">
            Authoritative, immutable event timeline of all AI & system actions.
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-bgCard border border-borderColor rounded-xl px-3 py-1.5 text-xs font-medium text-textColor">
            <Calendar className="w-3.5 h-3.5 text-subTextColor" />
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="bg-transparent outline-none cursor-pointer text-textColor font-semibold"
            >
              <option value={1}>Last 24 Hours</option>
              <option value={7}>Last 7 Days</option>
              <option value={14}>Last 14 Days</option>
              <option value={30}>Last 30 Days</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 bg-bgCard border border-borderColor rounded-xl px-3 py-1.5 text-xs font-medium text-textColor">
            <Filter className="w-3.5 h-3.5 text-subTextColor" />
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="bg-transparent outline-none cursor-pointer text-textColor font-semibold"
            >
              <option value="ALL">All Sources</option>
              <option value="AI_CHAT">AI Chat</option>
              <option value="AUTOMATION">Automation</option>
              <option value="DIRECT_UI">Direct UI</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center p-12 text-subTextColor text-sm font-medium">
          <Clock className="w-5 h-5 animate-spin mr-2 text-accent" /> Loading action history...
        </div>
      ) : events.length === 0 ? (
        <div className="text-center p-12 bg-bgCard border border-borderColor rounded-2xl">
          <History className="w-12 h-12 text-subTextColor mx-auto mb-3 opacity-40" />
          <h3 className="text-base font-semibold text-textColor">No AI actions found for this period</h3>
          <p className="text-xs text-subTextColor mt-1">Actions executed through AI Chat or Automations will appear here automatically.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {events.map((ev) => (
            <div key={ev.id} className="bg-bgCard border border-borderColor rounded-2xl p-4 transition-all hover:border-accent/40 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <div className="p-2.5 rounded-xl bg-accent/10 text-accent mt-0.5">
                  {ev.source_type === 'AI_CHAT' ? (
                    <Bot className="w-5 h-5" />
                  ) : ev.source_type === 'AUTOMATION' ? (
                    <Clock className="w-5 h-5" />
                  ) : (
                    <User className="w-5 h-5" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-textColor">
                      {ev.reason || ev.action_type.replace(/_/g, ' ')}
                    </span>
                    {renderStatusBadge(ev.status)}
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface border border-borderColor text-subTextColor">
                      {ev.source_type}
                    </span>
                  </div>
                  <p className="text-xs text-subTextColor mt-1">
                    Target: <span className="font-semibold text-textColor">{ev.target_type}</span> {ev.target_id ? `(${ev.target_id.substring(0, 8)}...)` : ''}
                  </p>
                </div>
              </div>

              <div className="text-right text-xs text-subTextColor flex flex-col justify-center items-end">
                <span>{ev.created_at ? new Date(ev.created_at).toLocaleString() : 'N/A'}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
export default ActionHistoryPage;
