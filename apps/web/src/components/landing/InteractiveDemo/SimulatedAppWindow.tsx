import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Search, Sparkles, User, ShieldCheck } from 'lucide-react';
import { DemoSidebar } from './DemoSidebar';
import { DemoDashboardView, WorkspaceData } from './DemoDashboardView';
import { DemoSearchSimulator } from './DemoSearchSimulator';
import { DemoAIChatSimulator } from './DemoAIChatSimulator';
import { DemoDocPreviewModal, DemoDoc } from './DemoDocPreviewModal';
import { Badge } from '../foundation/feedback/Badge';

// Mock Workspaces Data
const MOCK_WORKSPACES: WorkspaceData[] = [
  {
    name: 'Engineering R&D',
    projectsCount: 14,
    documentsCount: 98,
    decisionsCount: 42,
    recentDocs: [
      {
        id: 'e1',
        name: 'architecture_specification_v2.md',
        type: 'markdown',
        size: '24 KB',
        updatedAt: '2 hours ago',
        author: 'Principal Architect',
        content: '# Architecture Spec v2\nApproved 15-min JWT access token duration with 30-day sliding refresh token.',
        citations: 18,
      },
      {
        id: 'e2',
        name: 'security_soc2_compliance.pdf',
        type: 'pdf',
        size: '4.8 MB',
        updatedAt: 'Yesterday',
        author: 'Security Ops',
        content: 'SOC2 Type II Audit Report: MindMesh encryption and access controls verified.',
        citations: 24,
      },
    ],
    activities: [
      { id: 'a1', action: 'Indexed architecture_specification_v2.md', time: '10m ago', user: 'AI Vector Indexer' },
      { id: 'a2', action: 'Extracted Decision #42: Refresh Token Sliding Duration', time: '1h ago', user: 'Graph Engine' },
    ],
  },
  {
    name: 'Product & Design',
    projectsCount: 8,
    documentsCount: 54,
    decisionsCount: 26,
    recentDocs: [
      {
        id: 'p1',
        name: 'q3_user_experience_roadmap.md',
        type: 'markdown',
        size: '18 KB',
        updatedAt: '1 day ago',
        author: 'Product Lead',
        content: '# Product Roadmap Q3\n1. Vector Search Simulator\n2. Mobile Drawer Navigation',
        citations: 12,
      },
    ],
    activities: [
      { id: 'a3', action: 'Created Project: Design System v2', time: '3h ago', user: 'Product Lead' },
    ],
  },
  {
    name: 'Marketing & Growth',
    projectsCount: 6,
    documentsCount: 32,
    decisionsCount: 14,
    recentDocs: [
      {
        id: 'm1',
        name: 'brand_positioning_guidelines.pdf',
        type: 'pdf',
        size: '2.1 MB',
        updatedAt: '3 days ago',
        author: 'Growth Lead',
        content: 'MindMesh Brand Positioning: AI-Powered Knowledge Intelligence System.',
        citations: 9,
      },
    ],
    activities: [
      { id: 'a4', action: 'Uploaded brand_positioning_guidelines.pdf', time: '5h ago', user: 'Growth Lead' },
    ],
  },
  {
    name: 'Legal & Compliance',
    projectsCount: 4,
    documentsCount: 65,
    decisionsCount: 31,
    recentDocs: [
      {
        id: 'l1',
        name: 'vendor_data_privacy_addendum.pdf',
        type: 'pdf',
        size: '3.6 MB',
        updatedAt: '4 days ago',
        author: 'General Counsel',
        content: 'Data Privacy Addendum: GDPR and CCPA compliant workspace isolation.',
        citations: 16,
      },
    ],
    activities: [
      { id: 'a5', action: 'Approved SOC2 Control Assessment', time: '1d ago', user: 'General Counsel' },
    ],
  },
];

export const SimulatedAppWindow: React.FC = () => {
  const [currentWorkspace, setCurrentWorkspace] = useState<WorkspaceData>(MOCK_WORKSPACES[0]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedDoc, setSelectedDoc] = useState<DemoDoc | null>(null);
  const [isDocModalOpen, setIsDocModalOpen] = useState(false);

  const handlePreviewDoc = (doc: DemoDoc) => {
    setSelectedDoc(doc);
    setIsDocModalOpen(true);
  };

  return (
    <div className="w-full rounded-ds-2xl overflow-hidden bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800/90 shadow-2xl text-slate-900 dark:text-slate-100 flex flex-col md:flex-row min-h-[620px]">
      {/* Interactive Sidebar */}
      <DemoSidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        currentWorkspace={currentWorkspace}
        workspaces={MOCK_WORKSPACES}
        onSelectWorkspace={setCurrentWorkspace}
      />

      {/* Main App Content View Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-slate-50/50 dark:bg-slate-950">
        {/* Topbar Header */}
        <div className="flex items-center justify-between px-6 py-3.5 bg-slate-100/90 dark:bg-slate-900/90 border-b border-slate-200 dark:border-slate-800 backdrop-blur-md select-none text-xs">
          <div className="flex items-center gap-3">
            <span className="font-bold text-slate-900 dark:text-white uppercase font-mono tracking-wider">
              {currentWorkspace.name}
            </span>
            <Badge variant="primary" className="text-[10px]">
              Live Grounded Index
            </Badge>
          </div>


          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => alert('Simulated notification drawer')}
              className="p-1.5 rounded-ds-md hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <Bell className="w-4 h-4" />
            </button>
            <div className="w-7 h-7 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center text-[10px]">
              MM
            </div>
          </div>
        </div>

        {/* View Router Display Area */}
        <div className="p-4 mobile-sm:p-6 lg:p-8 flex-1 overflow-y-auto">
          <AnimatePresence mode="wait">
            {activeTab === 'dashboard' && (
              <motion.div
                key="dashboard"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <DemoDashboardView workspace={currentWorkspace} onPreviewDoc={handlePreviewDoc} />
              </motion.div>
            )}

            {activeTab === 'search' && (
              <motion.div
                key="search"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <DemoSearchSimulator onPreviewDoc={handlePreviewDoc} />
              </motion.div>
            )}

            {activeTab === 'chat' && (
              <motion.div
                key="chat"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <DemoAIChatSimulator />
              </motion.div>
            )}

            {(activeTab === 'documents' || activeTab === 'files' || activeTab === 'workspaces' || activeTab === 'settings') && (
              <motion.div
                key="fallback"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <DemoDashboardView workspace={currentWorkspace} onPreviewDoc={handlePreviewDoc} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Document Preview Modal */}
      <DemoDocPreviewModal
        doc={selectedDoc}
        isOpen={isDocModalOpen}
        onClose={() => setIsDocModalOpen(false)}
      />
    </div>
  );
};
