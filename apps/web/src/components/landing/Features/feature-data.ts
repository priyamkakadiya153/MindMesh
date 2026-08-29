import React from 'react';
import {
  Cpu,
  Database,
  Search,
  Zap,
  Users,
  ShieldCheck,
  Building,
} from 'lucide-react';

export interface FeatureItem {
  name: string;
  description: string;
}

export interface FeatureCategory {
  id: string;
  title: string;
  badge: string;
  summary: string;
  description: string;
  iconName: string;
  features: FeatureItem[];
  metricLabel: string;
  metricValue: string;
}

export const FEATURE_CATEGORIES: FeatureCategory[] = [
  {
    id: 'ai-intelligence',
    title: 'AI Intelligence',
    badge: 'Grounded RAG',
    summary: 'Context-aware AI Grounded on Your Team’s Memory',
    description:
      'MindMesh uses Retrieval-Augmented Generation (RAG) to answer complex technical queries using 100% cited workspace files, chats, and decisions with zero hallucinations.',
    iconName: 'Cpu',
    metricLabel: 'Grounded Accuracy',
    metricValue: '100% Cited',
    features: [
      { name: 'Context-Aware AI Chat', description: 'Ask questions in natural language and receive instant, grounded responses.' },
      { name: 'Document Understanding', description: 'Extract key insights, summaries, and action items from complex PDFs and Markdown.' },
      { name: 'Source Citation Cards', description: 'Every AI response links directly to exact workspace source files and message timestamps.' },
      { name: 'Automatic Summarization', description: 'Generate executive summaries of lengthy team threads and technical design documents.' },
    ],
  },
  {
    id: 'knowledge-management',
    title: 'Knowledge Management',
    badge: 'Structured Graph',
    summary: 'Turn Scattered Files into Organized Institutional Memory',
    description:
      'Stop losing track of critical documentation. MindMesh automatically categorizes, parses, and connects PDFs, DOCX, Markdown, and codebase repositories.',
    iconName: 'Database',
    metricLabel: 'Format Support',
    metricValue: 'PDF, MD, Code & Docs',
    features: [
      { name: 'Universal File Parsing', description: 'Automatic metadata extraction and content indexing for all document types.' },
      { name: 'Workspace Folder Hierarchies', description: 'Flexible folder structures with project tags and document cross-referencing.' },
      { name: 'Version History & Lineage', description: 'Track document evolution and see who authored key architectural changes.' },
      { name: 'Knowledge Graph Indexing', description: 'Interconnected graph mapping relationships between files, chats, and tasks.' },
    ],
  },
  {
    id: 'universal-search',
    title: 'Universal Search',
    badge: '0.04s Vector Lookup',
    summary: 'Find Anything Across Your Entire Organization Instantly',
    description:
      'Search by intent rather than exact string matching. Our vector engine understands synonyms, typos, and phrasing gaps with sub-second response times.',
    iconName: 'Search',
    metricLabel: 'Query Latency',
    metricValue: '0.04s Average',
    features: [
      { name: 'Natural Language Queries', description: 'Search using conversational questions like "What did we decide about auth tokens?"' },
      { name: 'Hybrid Semantic & Keyword Search', description: 'Combines vector semantic similarity with precise keyword matching.' },
      { name: 'Filter & Search History', description: 'Filter search by workspace, author, document type, and date range.' },
      { name: 'Instant Search Auto-Suggestions', description: 'Real-time typeahead suggestions as you type.' },
    ],
  },
  {
    id: 'automation',
    title: 'Automation',
    badge: 'Auto Extraction',
    summary: 'Background Decision Extraction & Smart Workflows',
    description:
      'MindMesh continuously monitors discussion threads in the background, automatically detecting architectural decisions and converting them into actionable task nodes.',
    iconName: 'Zap',
    metricLabel: 'Task Extraction',
    metricValue: 'Automatic',
    features: [
      { name: 'Background AI Indexing', description: 'Continuous vector embedding generation as new documents and chats are added.' },
      { name: 'Automatic Decision Extraction', description: 'Detects key decisions inside chat discussions and logs them in the decision graph.' },
      { name: 'Smart Event Triggers', description: 'Receive automated alerts when relevant documentation or decisions are updated.' },
      { name: 'Activity Stream Sync', description: 'Real-time timeline tracking all knowledge updates across the organization.' },
    ],
  },
  {
    id: 'collaboration',
    title: 'Collaboration',
    badge: 'Real-Time Team Sync',
    summary: 'Unify Team Communication with Document Context',
    description:
      'Connect direct messages, project channels, and document editing in one place. Keep teams aligned on a single source of truth.',
    iconName: 'Users',
    metricLabel: 'Team Alignment',
    metricValue: 'Single Source of Truth',
    features: [
      { name: 'Team Workspaces & Channels', description: 'Dedicated spaces for Engineering, Product, Marketing, and Legal teams.' },
      { name: 'Contextual Direct Messages', description: 'Chat with teammates right alongside referenced documents and project tasks.' },
      { name: 'Mentions & Real-Time Presence', description: 'Notify teammates and see active contributors across workspaces.' },
      { name: 'Collaborative Activity Stream', description: 'Stay up to date on recently added files, chats, and decisions.' },
    ],
  },
  {
    id: 'security',
    title: 'Security',
    badge: 'SOC2 Ready',
    summary: 'Enterprise-Grade Protection & Tenant Isolation',
    description:
      'Built for enterprise compliance with SOC2 Type II controls, AES-256 encryption at rest, TLS 1.3 in transit, and strict Role-Based Access Control (RBAC).',
    iconName: 'ShieldCheck',
    metricLabel: 'Encryption Standard',
    metricValue: 'AES-256 & TLS 1.3',
    features: [
      { name: 'Role-Based Access Control (RBAC)', description: 'Granular permissions for Owners, Admins, Members, and Guests.' },
      { name: 'Tenant Data Isolation', description: 'Strict workspace data boundaries ensuring zero cross-tenant leakage.' },
      { name: 'Audit Logs & Governance', description: 'Detailed logs tracking document views, queries, exports, and permissions.' },
      { name: 'Session & Token Revocation', description: 'Instant single-device or global session revocation capabilities.' },
    ],
  },
  {
    id: 'enterprise',
    title: 'Enterprise',
    badge: 'Multi-Tenant Scale',
    summary: 'Scalable Architecture for Growing Organizations',
    description:
      'Manage multiple organizations, hundreds of workspaces, and thousands of team members with comprehensive administration tools and storage analytics.',
    iconName: 'Building',
    metricLabel: 'Architecture Scale',
    metricValue: 'Unlimited Workspaces',
    features: [
      { name: 'Multi-Organization Management', description: 'Switch seamlessly between distinct enterprise organizations.' },
      { name: 'Member & Seat Administration', description: 'Centralized directory for managing user invites, roles, and access.' },
      { name: 'Storage & Query Analytics', description: 'Monitor vector storage usage, document counts, and query volume.' },
      { name: 'Enterprise SLA & Dedicated Support', description: '99.9% uptime SLA guarantee with high-priority support.' },
    ],
  },
];
