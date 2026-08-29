import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  UploadCloud,
  Layers,
  Cpu,
  Search,
  Zap,
  CheckCircle2,
  FileText,
  MessageSquare,
  Sparkles,
  ArrowRight,
  Shield,
  Bot,
  Brain,
} from 'lucide-react';
import { Card } from '../foundation/layout/Card';
import { Badge } from '../foundation/feedback/Badge';
import { Heading, Text } from '../foundation/typography/Typography';

export interface StageDetail {
  id: number;
  key: string;
  stageName: string;
  badge: string;
  headline: string;
  description: string;
  icon: React.ReactNode;
  highlights: string[];
  previewWidget: React.ReactNode;
}

export const STAGE_DETAILS: StageDetail[] = [
  {
    id: 1,
    key: 'capture',
    stageName: 'Step 1: Capture',
    badge: 'Universal Ingestion',
    headline: 'Information Flows In Seamlessly',
    description:
      'Upload PDFs, DOCX, Markdown, images, and codebase repositories. Connect team Slack, Teams, and meeting transcripts into one frictionless platform.',
    icon: <UploadCloud className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />,
    highlights: ['Multi-format file parsing', 'Real-time chat ingestion', 'Zero manual data entry'],
    previewWidget: (
      <div className="p-4 rounded-ds-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
        <div className="flex items-center justify-between p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="flex items-center gap-2 text-slate-800 dark:text-slate-200 font-medium">
            <FileText className="w-4 h-4 text-indigo-600 dark:text-indigo-400" /> enterprise_operating_model.pdf
          </span>
          <Badge variant="success" className="text-[9px]">Uploaded</Badge>
        </div>
        <div className="flex items-center justify-between p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="flex items-center gap-2 text-slate-800 dark:text-slate-200 font-medium">
            <MessageSquare className="w-4 h-4 text-purple-600 dark:text-purple-400" /> Slack #architecture-sync
          </span>
          <Badge variant="primary" className="text-[9px]">Streamed</Badge>
        </div>
      </div>
    ),
  },
  {
    id: 2,
    key: 'organize',
    stageName: 'Step 2: Organize',
    badge: 'Intelligent Structuring',
    headline: 'Scattered Data Becomes Structured Context',
    description:
      'MindMesh categorizes content into Workspaces, Projects, and Tag taxonomies with automatic RBAC permissions and file relationship graph mapping.',
    icon: <Layers className="w-6 h-6 text-blue-600 dark:text-blue-400" />,
    highlights: ['Automated tag hierarchy', 'RBAC & Org boundaries', 'Project cross-linking'],
    previewWidget: (
      <div className="p-4 rounded-ds-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
        <div className="p-2.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <span className="font-semibold text-slate-900 dark:text-white">Workspace: Engineering R&D</span>
          <span className="text-[10px] font-mono text-indigo-600 dark:text-indigo-400 font-bold">14 Projects</span>
        </div>
        <div className="flex gap-2">
          <span className="px-2 py-1 rounded bg-indigo-50 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 text-[10px] font-medium">#Architecture</span>
          <span className="px-2 py-1 rounded bg-emerald-50 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-[10px] font-medium">#Security-Audit</span>
        </div>
      </div>
    ),
  },
  {
    id: 3,
    key: 'understand',
    stageName: 'Step 3: Understand',
    badge: 'Semantic Vector AI',
    headline: 'The AI Vector & Graph Memory Layer',
    description:
      'MindMesh parses semantic intent, extracts decisions from chat threads, runs OCR on scanned files, and links concepts into a living knowledge graph.',
    icon: <Cpu className="w-6 h-6 text-purple-600 dark:text-purple-400" />,
    highlights: ['Embedding vector indexing', 'Automatic decision extraction', 'Multi-modal OCR parsing'],
    previewWidget: (
      <div className="p-4 rounded-ds-xl bg-slate-50 dark:bg-slate-950 border border-indigo-200 dark:border-indigo-500/30 space-y-2 text-xs">
        <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold">
          <Brain className="w-4 h-4" /> Vector Graph Embeddings
        </div>
        <p className="text-[11px] text-slate-700 dark:text-slate-300 font-medium">
          Extracted 42 decision nodes and linked 98 PDF spec chunks.
        </p>
      </div>
    ),
  },
  {
    id: 4,
    key: 'retrieve',
    stageName: 'Step 4: Retrieve',
    badge: 'Sub-Second Search',
    headline: 'Ask Natural Questions. Get Instant Answers.',
    description:
      'Query your organizational memory in natural language. Get 0.04s vector search responses backed by 100% cited workspace sources.',
    icon: <Search className="w-6 h-6 text-cyan-600 dark:text-cyan-400" />,
    highlights: ['0.04s Vector lookup speed', 'Natural language queries', 'Zero data hallucination'],
    previewWidget: (
      <div className="p-4 rounded-ds-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
        <div className="p-2.5 rounded bg-indigo-50/80 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-500/30 text-slate-800 dark:text-slate-200 font-mono">
          Q: "What is our JWT token expiration policy?"
        </div>
        <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
          <CheckCircle2 className="w-3.5 h-3.5" /> Found in 3 cited sources (0.04s)
        </div>
      </div>
    ),
  },
  {
    id: 5,
    key: 'act',
    stageName: 'Step 5: Act',
    badge: 'Actionable Intelligence',
    headline: 'Knowledge Becomes Execution',
    description:
      'Accelerate new hire onboarding from months to days. Automate project task tracking and keep teams aligned with trusted organizational context.',
    icon: <Zap className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />,
    highlights: ['60% faster onboarding', 'Automated task execution', 'Aligned team decision memory'],
    previewWidget: (
      <div className="p-4 rounded-ds-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
        <div className="flex items-center justify-between p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <span className="text-slate-900 dark:text-white font-medium">Action: Enforce 15-min JWT session</span>
          <Badge variant="success" className="text-[9px]">Assigned</Badge>
        </div>
      </div>
    ),
  },
];

export interface SolutionCardListProps {
  activeStep: number;
  onSelectStep: (stepId: number) => void;
}

export const SolutionCardList: React.FC<SolutionCardListProps> = ({
  activeStep,
  onSelectStep,
}) => {
  const currentStage = STAGE_DETAILS.find((s) => s.id === activeStep) || STAGE_DETAILS[0];

  return (
    <div className="w-full max-w-5xl mx-auto">
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStage.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
        >
          <Card variant="interactive" className="p-6 sm:p-8 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-ds-medium text-left">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              {/* Left Stage Details */}
              <div className="lg:col-span-7 space-y-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-ds-xl bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-200 dark:border-indigo-500/30">
                    {currentStage.icon}
                  </div>
                  <div>
                    <span className="text-xs font-bold font-mono text-indigo-600 dark:text-indigo-400 block uppercase tracking-wider">
                      {currentStage.stageName}
                    </span>
                    <Badge variant="primary" className="text-[10px] mt-0.5">
                      {currentStage.badge}
                    </Badge>
                  </div>
                </div>

                <Heading level="h3" className="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white">
                  {currentStage.headline}
                </Heading>

                <Text variant="body" muted className="text-slate-600 dark:text-slate-300 leading-relaxed">
                  {currentStage.description}
                </Text>

                {/* Key Highlights Checklist */}
                <div className="space-y-2 pt-2">
                  {currentStage.highlights.map((h) => (
                    <div key={h} className="flex items-center gap-2 text-xs font-semibold text-slate-800 dark:text-slate-200">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                      <span>{h}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Right Mini Interactive Preview Graphic */}
              <div className="lg:col-span-5 space-y-4">
                <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-left">
                  Stage Live Indicator
                </div>
                {currentStage.previewWidget}
              </div>
            </div>
          </Card>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};
