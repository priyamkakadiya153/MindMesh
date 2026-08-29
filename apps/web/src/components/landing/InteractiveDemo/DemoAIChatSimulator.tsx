import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, User, Sparkles, FileText, CheckCircle2, Send, CornerDownLeft } from 'lucide-react';
import { Badge } from '../foundation/feedback/Badge';
import { Button } from '../foundation/buttons/Button';

export interface ChatPreset {
  id: string;
  prompt: string;
  response: string;
  citations: Array<{ title: string; type: string }>;
}

const CHAT_PRESETS: ChatPreset[] = [
  {
    id: '1',
    prompt: 'Summarize yesterday’s architecture meeting',
    response:
      'In yesterday’s sync, the team approved the 15-minute JWT access token duration with 30-day sliding refresh tokens. Single-device session revocation endpoints were prioritized for Q3 release.',
    citations: [
      { title: 'architecture_sync_august_2026.md', type: 'Meeting Notes' },
      { title: 'auth_security_specification_v2.pdf', type: 'PDF Document' },
    ],
  },
  {
    id: '2',
    prompt: 'What are our SOC2 compliance requirements?',
    response:
      'MindMesh enforces AES-256 data encryption at rest and TLS 1.3 in transit. RBAC policies isolate workspace tenant data with zero data leakage across organization boundaries.',
    citations: [
      { title: 'soc2_type_ii_audit_report.pdf', type: 'Audit PDF' },
      { title: 'security_governance_policy.md', type: 'Markdown Policy' },
    ],
  },
  {
    id: '3',
    prompt: 'Explain our database migration plan',
    response:
      'PostgreSQL schema DDL migrations execute zero-downtime column additions with backwards-compatible service APIs and automated rollback triggers.',
    citations: [
      { title: 'database_migration_v4_guide.md', type: 'Migration Plan' },
      { title: 'apply_schema_ddl.py', type: 'Python Script' },
    ],
  },
];

export const DemoAIChatSimulator: React.FC = () => {
  const [activePreset, setActivePreset] = useState<ChatPreset>(CHAT_PRESETS[0]);
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    setIsTyping(true);
    setDisplayedText('');
    let index = 0;

    const interval = setInterval(() => {
      if (index < activePreset.response.length) {
        setDisplayedText((prev) => prev + activePreset.response.charAt(index));
        index++;
      } else {
        setIsTyping(false);
        clearInterval(interval);
      }
    }, 15);

    return () => clearInterval(interval);
  }, [activePreset]);

  return (
    <div className="space-y-6 text-left">
      {/* Sample Prompt Chips */}
      <div className="space-y-2">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Ask MindMesh AI Assistant:</span>
        <div className="flex flex-wrap gap-2">
          {CHAT_PRESETS.map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => setActivePreset(preset)}
              className={`text-xs px-3 py-1.5 rounded-ds-pill font-medium transition-all border ${
                activePreset.id === preset.id
                  ? 'bg-indigo-600 text-white border-indigo-500 shadow-ds-soft'
                  : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-400 border-slate-200 dark:border-slate-800 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              "{preset.prompt}"
            </button>
          ))}
        </div>
      </div>

      {/* Simulated Chat Window */}
      <div className="p-4 sm:p-6 rounded-ds-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-5 shadow-ds-medium">
        {/* User Prompt Message */}
        <div className="flex items-start gap-3 justify-end">
          <div className="p-3 rounded-ds-2xl rounded-tr-none bg-indigo-600 text-white text-xs font-medium max-w-md shadow-ds-soft">
            {activePreset.prompt}
          </div>
          <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold shrink-0 text-xs">
            <User className="w-4 h-4" />
          </div>
        </div>

        {/* AI Assistant Response */}
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold shrink-0 text-xs shadow-ds-soft">
            <Bot className="w-4 h-4" />
          </div>

          <div className="p-4 rounded-ds-2xl rounded-tl-none bg-white dark:bg-slate-900/90 border border-indigo-200 dark:border-indigo-500/30 text-slate-900 dark:text-slate-200 text-xs leading-relaxed space-y-3 max-w-lg shadow-ds-soft">
            <div className="flex items-center justify-between">
              <span className="font-bold text-indigo-600 dark:text-indigo-400 flex items-center gap-1 text-[11px]">
                <Sparkles className="w-3.5 h-3.5" /> MindMesh Grounded Synthesis
              </span>
              <Badge variant="success" className="text-[9px]">
                {isTyping ? 'Generating...' : '100% Grounded'}
              </Badge>
            </div>

            <p className="font-sans text-slate-800 dark:text-slate-200">{displayedText}</p>

            {/* Source Citations */}
            {!isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="pt-2 border-t border-slate-200 dark:border-slate-800 space-y-1.5"
              >
                <span className="text-[10px] uppercase font-bold text-slate-500 dark:text-slate-400 tracking-wider">
                  Cited Workspace Sources:
                </span>
                <div className="flex flex-wrap gap-2">
                  {activePreset.citations.map((c) => (
                    <span
                      key={c.title}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-[10px] text-indigo-700 dark:text-indigo-300 font-mono"
                    >
                      <FileText className="w-3 h-3 text-indigo-600 dark:text-indigo-400" />
                      {c.title}
                    </span>
                  ))}
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
};
