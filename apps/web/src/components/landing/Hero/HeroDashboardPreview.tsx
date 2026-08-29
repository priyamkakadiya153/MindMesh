import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  Sparkles,
  Database,
  FileText,
  MessageSquare,
  CheckCircle,
  Network,
  ArrowRight,
  Shield,
  Clock,
  Layers,
  ChevronRight,
  User,
  Bot,
} from 'lucide-react';
import { Badge } from '../foundation/feedback/Badge';
import { Chip } from '../foundation/feedback/Chip';

export type PreviewTab = 'search' | 'graph' | 'files' | 'tasks';

interface SearchResult {
  id: string;
  title: string;
  source: string;
  type: 'chat' | 'doc' | 'decision';
  snippet: string;
  score: string;
}

const SAMPLE_QUERIES = [
  'What did we decide about auth token expiration?',
  'Where is the SOC2 security audit document?',
  'Show recent frontend architecture decisions',
];

const SEARCH_DATA: Record<string, { answer: string; results: SearchResult[] }> = {
  default: {
    answer:
      'Based on yesterday’s Engineering Sync, JWT Access Tokens expire in 15 minutes and Refresh Tokens persist for 30 days with sliding session revocation.',
    results: [
      {
        id: '1',
        title: 'Engineering Sync Meeting Notes',
        source: 'Slack #architecture-sync',
        type: 'chat',
        snippet: 'Decided to enforce 15-min JWT access token duration with sliding refresh token.',
        score: '99.4% match',
      },
      {
        id: '2',
        title: 'auth_security_specification_v2.pdf',
        source: 'Knowledge Library',
        type: 'doc',
        snippet: 'Security Policy: Access tokens signed via RS256 with rotation strategy.',
        score: '96.2% match',
      },
      {
        id: '3',
        title: 'Decision #42: Session Revocation Strategy',
        source: 'Extracted Decision Graph',
        type: 'decision',
        snippet: 'Single-device session revocation endpoint implemented in API gateway.',
        score: '94.8% match',
      },
    ],
  },
};

export const HeroDashboardPreview: React.FC = () => {
  const [activeTab, setActiveTab] = useState<PreviewTab>('search');
  const [searchQuery, setSearchQuery] = useState(SAMPLE_QUERIES[0]);
  const [isSearching, setIsSearching] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 300, y: 200 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  const handleQueryClick = (query: string) => {
    setSearchQuery(query);
    setIsSearching(true);
    setTimeout(() => setIsSearching(false), 300);
  };

  const currentData = SEARCH_DATA.default;

  return (
    <motion.div
      initial={{ y: 0 }}
      animate={{ y: [0, -6, 0] }}
      transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
      onMouseMove={handleMouseMove}
      className="relative w-full rounded-ds-2xl overflow-hidden bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800/90 shadow-2xl text-slate-900 dark:text-slate-100 group"
    >
      {/* Mouse-Follow Spotlight Radial Glow Overlay */}
      <div
        className="pointer-events-none absolute inset-0 transition-opacity duration-300 opacity-60 group-hover:opacity-100 -z-0"
        style={{
          background: `radial-gradient(600px circle at ${mousePos.x}px ${mousePos.y}px, rgba(99, 102, 241, 0.15), transparent 70%)`,
        }}
      />

      {/* Top Browser / macOS Window Frame */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-100/90 dark:bg-slate-900/90 border-b border-slate-200 dark:border-slate-800/80 backdrop-blur-md select-none">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
          <div className="w-3 h-3 rounded-full bg-green-500/80" />
          <span className="ml-2 text-xs font-medium text-slate-500 dark:text-slate-400 font-mono hidden sm:inline">
            mindmesh.app/workspace/intelligence
          </span>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 bg-slate-200/80 dark:bg-slate-950/60 p-1 rounded-ds-md border border-slate-300 dark:border-slate-800 text-xs">
          <button
            type="button"
            onClick={() => setActiveTab('search')}
            className={`px-2.5 py-1 rounded-ds-sm font-medium transition-all ${
              activeTab === 'search'
                ? 'bg-indigo-600 text-white shadow-ds-soft'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            AI Search
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('graph')}
            className={`px-2.5 py-1 rounded-ds-sm font-medium transition-all ${
              activeTab === 'graph'
                ? 'bg-indigo-600 text-white shadow-ds-soft'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Knowledge Graph
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('files')}
            className={`px-2.5 py-1 rounded-ds-sm font-medium transition-all ${
              activeTab === 'files'
                ? 'bg-indigo-600 text-white shadow-ds-soft'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Files
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('tasks')}
            className={`px-2.5 py-1 rounded-ds-sm font-medium transition-all ${
              activeTab === 'tasks'
                ? 'bg-indigo-600 text-white shadow-ds-soft'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Decisions
          </button>
        </div>
      </div>

      {/* Main Preview Body */}
      <div className="p-4 mobile-sm:p-6 lg:p-8 space-y-6">
        {/* Interactive Search Bar */}
        <div className="relative">
          <div className="relative flex items-center w-full rounded-ds-xl bg-slate-50 dark:bg-slate-900/90 border border-slate-200 dark:border-indigo-500/40 shadow-ds-glow focus-within:border-indigo-500 transition-all overflow-hidden">
            <div className="pl-4 text-indigo-600 dark:text-indigo-400">
              <Search className="w-5 h-5" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Ask anything about your team's conversations, files, or decisions..."
              className="w-full py-3.5 pl-3 pr-24 bg-transparent text-sm font-medium text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none"
            />

            <div className="absolute right-3 flex items-center gap-1.5">
              <span className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-500/20 rounded border border-indigo-200 dark:border-indigo-500/30 font-medium">
                <Sparkles className="w-3 h-3 text-indigo-600 dark:text-indigo-400" /> Vector Grounded
              </span>
            </div>
          </div>

          {/* Sample Query Chips */}
          <div className="flex items-center gap-2 mt-3 overflow-x-auto no-scrollbar pb-1">
            <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 shrink-0">Try asking:</span>
            {SAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => handleQueryClick(q)}
                className={`text-xs px-2.5 py-1 rounded-ds-pill whitespace-nowrap transition-all border shrink-0 ${
                  searchQuery === q
                    ? 'bg-indigo-50 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 border-indigo-300 dark:border-indigo-500/40 font-semibold'
                    : 'bg-white dark:bg-slate-900/60 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                "{q}"
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content Display */}
        <AnimatePresence mode="wait">
          {activeTab === 'search' && (
            <motion.div
              key="search"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="space-y-4"
            >
              {/* AI Synthesized Answer Card */}
              <div className="p-4 sm:p-5 rounded-ds-xl bg-gradient-to-br from-indigo-50/90 via-white to-purple-50/90 dark:from-indigo-950/40 dark:via-slate-900/60 dark:to-purple-950/40 border border-indigo-200 dark:border-indigo-500/30 shadow-ds-soft relative">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 text-xs font-bold uppercase tracking-wider">
                    <Bot className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                    <span>MindMesh Synthesis Engine</span>
                  </div>
                  <Badge variant="primary" className="text-[10px]">
                    100% Grounded
                  </Badge>
                </div>
                <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-normal">
                  {currentData.answer}
                </p>
              </div>

              {/* Vector Match Source Cards */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-400 px-1">
                  <span>Cited Organizational Memory Sources</span>
                  <span>Semantic Confidence</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {currentData.results.map((res) => (
                    <div
                      key={res.id}
                      className="p-3 rounded-ds-lg bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 transition-all text-left space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase font-bold text-indigo-600 dark:text-indigo-400 tracking-wider">
                          {res.source}
                        </span>
                        <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
                          {res.score}
                        </span>
                      </div>
                      <h5 className="text-xs font-bold text-slate-900 dark:text-slate-100 line-clamp-1">
                        {res.title}
                      </h5>
                      <p className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
                        {res.snippet}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'graph' && (
            <motion.div
              key="graph"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-6 rounded-ds-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 text-center space-y-4"
            >
              <div className="w-12 h-12 mx-auto rounded-full bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                <Network className="w-6 h-6 animate-pulse" />
              </div>
              <h4 className="text-base font-bold text-slate-900 dark:text-white">Live Knowledge Graph Nodes</h4>
              <p className="text-xs text-slate-600 dark:text-slate-400 max-w-md mx-auto">
                1,420 conversation nodes automatically linked to 98 knowledge documents and 42 project decisions.
              </p>
            </motion.div>
          )}

          {activeTab === 'files' && (
            <motion.div
              key="files"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-4 rounded-ds-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-2"
            >
              {[
                { name: 'enterprise_operating_model.pdf', size: '1.2 MB', type: 'PDF' },
                { name: 'architecture_specification_v2.md', size: '24 KB', type: 'Markdown' },
                { name: 'security_soc2_compliance.pdf', size: '4.8 MB', type: 'PDF' },
              ].map((f) => (
                <div
                  key={f.name}
                  className="flex items-center justify-between p-3 rounded-ds-md bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80 text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <FileText className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                    <span className="font-medium text-slate-800 dark:text-slate-200">{f.name}</span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">{f.size}</span>
                </div>
              ))}
            </motion.div>
          )}

          {activeTab === 'tasks' && (
            <motion.div
              key="tasks"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-4 rounded-ds-xl bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-2"
            >
              {[
                { task: 'Implement JWT refresh token sliding duration endpoint', status: 'Extracted' },
                { task: 'Enforce SOC2 role-based access control policies', status: 'In Progress' },
              ].map((t) => (
                <div
                  key={t.task}
                  className="flex items-center justify-between p-3 rounded-ds-md bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800/80 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    <span className="font-medium text-slate-800 dark:text-slate-200">{t.task}</span>
                  </div>
                  <Badge variant="success" className="text-[10px]">
                    {t.status}
                  </Badge>
                </div>
              ))}
            </motion.div>
          )}

        </AnimatePresence>
      </div>
    </motion.div>
  );
};

