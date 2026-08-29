import React, { useState } from 'react';
import { X, Calendar, Clock, Zap, Globe, Loader2 } from 'lucide-react';

interface AddTriggerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: any) => Promise<void>;
}

export const AddTriggerModal: React.FC<AddTriggerModalProps> = ({
  isOpen,
  onClose,
  onSubmit
}) => {
  const [triggerType, setTriggerType] = useState<'SCHEDULE' | 'EVENT'>('SCHEDULE');
  const [scheduleType, setScheduleType] = useState<'ONE_TIME' | 'DAILY' | 'WEEKLY' | 'WEEKDAYS' | 'MONTHLY'>('DAILY');
  const [timeStr, setTimeStr] = useState('09:00');
  const [dayOfWeek, setDayOfWeek] = useState('Monday');
  const [timezone, setTimezone] = useState('Asia/Kolkata');
  const [eventType, setEventType] = useState('DOCUMENT_ADDED');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const payload: any = {
      trigger_type: triggerType,
      timezone
    };

    if (triggerType === 'SCHEDULE') {
      payload.schedule_type = scheduleType;
      payload.time_str = timeStr;
      if (scheduleType === 'WEEKLY') {
        payload.day_of_week = dayOfWeek;
      }
    } else {
      payload.event_type = eventType;
    }

    try {
      await onSubmit(payload);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create trigger');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fadeIn font-outfit">
      <div className="bg-bgCard border border-borderColor rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 text-textPrimary">
        <div className="flex items-center justify-between border-b border-borderMuted pb-4">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-xl bg-accentSubtle text-accent flex items-center justify-center border border-accent/20">
              <Zap className="w-4 h-4" />
            </div>
            <h3 className="text-base font-bold">Add Agent Trigger</h3>
          </div>
          <button onClick={onClose} className="p-1 text-textMuted hover:text-textPrimary rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-xs text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Trigger Type */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-textSecondary uppercase tracking-wider">Trigger Category</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setTriggerType('SCHEDULE')}
                className={`py-2 px-3 text-xs font-medium rounded-xl border flex items-center justify-center gap-2 transition-all ${
                  triggerType === 'SCHEDULE'
                    ? 'bg-accent/15 border-accent text-accent'
                    : 'bg-bgInput border-borderColor text-textMuted hover:text-textPrimary'
                }`}
              >
                <Calendar className="w-3.5 h-3.5" />
                Schedule
              </button>
              <button
                type="button"
                onClick={() => setTriggerType('EVENT')}
                className={`py-2 px-3 text-xs font-medium rounded-xl border flex items-center justify-center gap-2 transition-all ${
                  triggerType === 'EVENT'
                    ? 'bg-accent/15 border-accent text-accent'
                    : 'bg-bgInput border-borderColor text-textMuted hover:text-textPrimary'
                }`}
              >
                <Zap className="w-3.5 h-3.5" />
                Event
              </button>
            </div>
          </div>

          {triggerType === 'SCHEDULE' ? (
            <>
              {/* Schedule Type */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-textSecondary">Frequency</label>
                <select
                  value={scheduleType}
                  onChange={(e: any) => setScheduleType(e.target.value)}
                  className="w-full bg-bgInput border border-borderColor rounded-xl px-3 py-2 text-xs focus:outline-hidden focus:border-accent text-textPrimary"
                >
                  <option value="DAILY">Every Day (Daily)</option>
                  <option value="WEEKLY">Weekly (Specific Day)</option>
                  <option value="WEEKDAYS">Every Weekday (Mon-Fri)</option>
                  <option value="MONTHLY">Monthly (1st of Month)</option>
                  <option value="ONE_TIME">One-Time Run</option>
                </select>
              </div>

              {scheduleType === 'WEEKLY' && (
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-textSecondary">Day of Week</label>
                  <select
                    value={dayOfWeek}
                    onChange={e => setDayOfWeek(e.target.value)}
                    className="w-full bg-bgInput border border-borderColor rounded-xl px-3 py-2 text-xs focus:outline-hidden focus:border-accent text-textPrimary"
                  >
                    <option value="Monday">Monday</option>
                    <option value="Tuesday">Tuesday</option>
                    <option value="Wednesday">Wednesday</option>
                    <option value="Thursday">Thursday</option>
                    <option value="Friday">Friday</option>
                    <option value="Saturday">Saturday</option>
                    <option value="Sunday">Sunday</option>
                  </select>
                </div>
              )}

              {/* Time */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-textSecondary">Execution Time</label>
                <div className="relative">
                  <Clock className="w-3.5 h-3.5 absolute left-3 top-3 text-textMuted" />
                  <input
                    type="time"
                    value={timeStr}
                    onChange={e => setTimeStr(e.target.value)}
                    className="w-full bg-bgInput border border-borderColor rounded-xl pl-9 pr-3 py-2 text-xs focus:outline-hidden focus:border-accent text-textPrimary"
                  />
                </div>
              </div>
            </>
          ) : (
            /* Event Type */
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-textSecondary">Workspace Event</label>
              <select
                value={eventType}
                onChange={e => setEventType(e.target.value)}
                className="w-full bg-bgInput border border-borderColor rounded-xl px-3 py-2 text-xs focus:outline-hidden focus:border-accent text-textPrimary"
              >
                <option value="DOCUMENT_ADDED">Document Added</option>
                <option value="MESSAGE_RECEIVED">Message Received (Debounced)</option>
                <option value="TASK_CREATED">Task Created</option>
                <option value="PROJECT_UPDATED">Project Updated</option>
              </select>
            </div>
          )}

          {/* Timezone */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-textSecondary">Timezone</label>
            <div className="relative">
              <Globe className="w-3.5 h-3.5 absolute left-3 top-3 text-textMuted" />
              <select
                value={timezone}
                onChange={e => setTimezone(e.target.value)}
                className="w-full bg-bgInput border border-borderColor rounded-xl pl-9 pr-3 py-2 text-xs focus:outline-hidden focus:border-accent text-textPrimary"
              >
                <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                <option value="UTC">UTC</option>
                <option value="America/New_York">America/New_York (EST)</option>
                <option value="Europe/London">Europe/London (GMT/BST)</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-borderMuted">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 text-xs font-medium text-textSecondary hover:text-textPrimary bg-bgInput hover:bg-bgHover border border-borderColor rounded-xl transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-1.5 text-xs font-semibold text-white bg-accent hover:bg-accent/90 rounded-xl shadow-xs transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Saving...
                </>
              ) : (
                'Add Trigger'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
