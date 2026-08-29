import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Sparkles, FileText, ArrowRight, Eye, CheckCircle2, Filter } from 'lucide-react';
import { Badge } from '../foundation/feedback/Badge';
import { Button } from '../foundation/buttons/Button';
import { DemoDoc } from './DemoDocPreviewModal';

export interface DemoSearchSimulatorProps {
  onPreviewDoc: (doc: DemoDoc) => void;
}

const SAMPLE_QUERIES = [
  'contract',
  'onboarding',
  'AI roadmap',
  'meeting notes',
  'invoice',
];

const MOCK_SEARCH_RESULTS: Record<string, DemoDoc[]> = {
  contract: [
    {
      id: 'c1',
      name: 'vendor_services_agreement_2026.pdf',
      type: 'pdf',
      size: '2.4 MB',
      updatedAt: '2 days ago',
      author: 'Legal Ops',
      content:
        'MASTER SERVICES AGREEMENT: Section 4.2 - MindMesh guarantees 99.9% uptime SLA with end-to-end AES-256 data encryption for all indexed workspace knowledge.',
      citations: 12,
    },
    {
      id: 'c2',
      name: 'soc2_type_ii_audit_report.pdf',
      type: 'pdf',
      size: '5.1 MB',
      updatedAt: '1 week ago',
      author: 'Security Compliance',
      content:
        'INDEPENDENT AUDITOR REPORT: MindMesh controls evaluated against Security, Confidentiality, and Availability Trust Services Criteria.',
      citations: 28,
    },
  ],
  onboarding: [
    {
      id: 'o1',
      name: 'engineering_onboarding_guide.md',
      type: 'markdown',
      size: '34 KB',
      updatedAt: 'Yesterday',
      author: 'Staff Tech Lead',
      content:
        '# Engineering Onboarding Guide\nWelcome to MindMesh Engineering! Follow these steps to configure your Python backend and Next.js web application locally.',
      citations: 45,
    },
  ],
  'ai roadmap': [
    {
      id: 'a1',
      name: 'q3_ai_intelligence_roadmap.md',
      type: 'markdown',
      size: '18 KB',
      updatedAt: '3 days ago',
      author: 'Product Director',
      content:
        '# Q3 Knowledge Intelligence Roadmap\n1. Graph RAG Citation Linking\n2. Real-time Slack/Teams Ingestion\n3. Autonomous Knowledge Digest Generation',
      citations: 31,
    },
  ],
  'meeting notes': [
    {
      id: 'm1',
      name: 'architecture_sync_august_2026.md',
      type: 'notes',
      size: '12 KB',
      updatedAt: '4 hours ago',
      author: 'Principal Architect',
      content:
        'DECISION RECORD: Approved 15-minute JWT access token with 30-day refresh token sliding duration. Implemented single-device session revocation API.',
      citations: 19,
    },
  ],
  invoice: [
    {
      id: 'i1',
      name: 'enterprise_cloud_invoice_q2.pdf',
      type: 'pdf',
      size: '420 KB',
      updatedAt: '5 days ago',
      author: 'Finance Ops',
      content:
        'INVOICE #MM-9042: MindMesh Enterprise Knowledge Plan - 250 Workspace Seats with Unlimited Semantic Search Indexing.',
      citations: 8,
    },
  ],
};

export const DemoSearchSimulator: React.FC<DemoSearchSimulatorProps> = ({
  onPreviewDoc,
}) => {
  const [query, setQuery] = useState('contract');

  const normalizedQuery = query.toLowerCase().trim();
  const matchedKey =
    Object.keys(MOCK_SEARCH_RESULTS).find((k) => normalizedQuery.includes(k)) || 'contract';

  const results = MOCK_SEARCH_RESULTS[matchedKey] || MOCK_SEARCH_RESULTS.contract;

  return (
    <div className="space-y-6">
      {/* Search Input Bar */}
      <div className="relative">
        <div className="relative flex items-center w-full rounded-ds-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-indigo-500/40 shadow-ds-glow focus-within:border-indigo-400 transition-all overflow-hidden">
          <div className="pl-4 text-indigo-600 dark:text-indigo-400">
            <Search className="w-5 h-5" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type 'contract', 'onboarding', 'AI roadmap', 'meeting notes'..."
            className="w-full py-3.5 pl-3 pr-28 bg-transparent text-sm font-medium text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none"
          />
          <div className="absolute right-3 flex items-center gap-2">
            <Badge variant="primary" className="text-[10px] font-mono">
              0.04s Vector
            </Badge>
          </div>
        </div>

        {/* Query Suggestion Chips */}
        <div className="flex items-center gap-2 mt-3 overflow-x-auto no-scrollbar pb-1">
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 shrink-0">Try typing:</span>
          {SAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => setQuery(q)}
              className={`text-xs px-2.5 py-1 rounded-ds-pill font-medium transition-all border shrink-0 ${
                query === q
                  ? 'bg-indigo-600 text-white border-indigo-500 shadow-ds-soft font-semibold'
                  : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-800 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              "{q}"
            </button>
          ))}
        </div>
      </div>

      {/* Vector Results Listing */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400">
          <span>{results.length} Vector Matches Found</span>
          <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1 font-mono">
            <CheckCircle2 className="w-3.5 h-3.5" /> 100% Grounded Context
          </span>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={matchedKey}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="space-y-3"
          >
            {results.map((doc) => (
              <div
                key={doc.id}
                className="p-4 rounded-ds-xl bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 hover:border-indigo-500/40 transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-left"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                    <span className="text-sm font-bold text-slate-900 dark:text-white">{doc.name}</span>
                    <Badge variant="secondary" className="text-[9px] uppercase font-mono">
                      {doc.type}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2 leading-relaxed font-sans">
                    {doc.content}
                  </p>
                  <div className="flex items-center gap-3 text-[10px] text-slate-500 font-mono pt-1">
                    <span>Author: {doc.author}</span>
                    <span>Updated: {doc.updatedAt}</span>
                    <span className="text-indigo-600 dark:text-indigo-400 font-semibold">{doc.citations} citations</span>
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  leftIcon={<Eye className="w-3.5 h-3.5" />}
                  onClick={() => onPreviewDoc(doc)}
                  className="shrink-0"
                >
                  Preview Document
                </Button>
              </div>
            ))}
          </motion.div>
        </AnimatePresence>
      </div>

    </div>
  );
};
