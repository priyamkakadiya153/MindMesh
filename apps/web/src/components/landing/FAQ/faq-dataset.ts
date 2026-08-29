export type FAQCategory =
  | 'getting-started'
  | 'ai-features'
  | 'documents'
  | 'workspaces'
  | 'security'
  | 'pricing'
  | 'enterprise'
  | 'technical';

export interface FAQItem {
  id: string;
  category: FAQCategory;
  categoryLabel: string;
  question: string;
  answer: string;
}

export const FAQ_CATEGORIES: Array<{ id: FAQCategory; label: string }> = [
  { id: 'getting-started', label: 'Getting Started' },
  { id: 'ai-features', label: 'AI Features' },
  { id: 'documents', label: 'Documents' },
  { id: 'workspaces', label: 'Workspaces' },
  { id: 'security', label: 'Security' },
  { id: 'pricing', label: 'Pricing' },
  { id: 'enterprise', label: 'Enterprise' },
  { id: 'technical', label: 'Technical' },
];


export const FAQ_DATABASE: FAQItem[] = [
  // Getting Started
  {
    id: 'gs-1',
    category: 'getting-started',
    categoryLabel: 'Getting Started',
    question: 'What is MindMesh?',
    answer:
      'MindMesh is an AI-powered Knowledge Intelligence System that transforms scattered files, chat discussions, project notes, and decisions into a living, searchable organizational memory.',
  },
  {
    id: 'gs-2',
    category: 'getting-started',
    categoryLabel: 'Getting Started',
    question: 'How does MindMesh work?',
    answer:
      'MindMesh automatically ingests PDFs, Markdown documents, codebase specs, and team chats. It indexes content using a sub-second 0.04s vector engine and builds an interconnected Knowledge Graph linking files to decisions.',
  },
  {
    id: 'gs-3',
    category: 'getting-started',
    categoryLabel: 'Getting Started',
    question: 'Can I use MindMesh for free?',
    answer:
      'Yes! MindMesh offers a Free plan forever that includes 5 Workspaces, 50 Knowledge Documents, 0.04s vector search, and context-aware AI chat.',
  },
  {
    id: 'gs-4',
    category: 'getting-started',
    categoryLabel: 'Getting Started',
    question: 'How quickly can I get started?',
    answer:
      'You can create a workspace and deploy MindMesh in under 60 seconds with no credit card required.',
  },

  // AI Features
  {
    id: 'ai-1',
    category: 'ai-features',
    categoryLabel: 'AI Features',
    question: 'How does AI Search work?',
    answer:
      'MindMesh uses natural language intent matching and hybrid sparse-dense vector embeddings to return relevant documents, chats, and decisions in 0.04s.',
  },
  {
    id: 'ai-2',
    category: 'ai-features',
    categoryLabel: 'AI Features',
    question: 'Does MindMesh use Retrieval-Augmented Generation (RAG)?',
    answer:
      'Yes, our RAG engine synthesizes answers exclusively from your team’s uploaded files and chat threads, attaching 100% cited source cards with zero hallucinations.',
  },
  {
    id: 'ai-3',
    category: 'ai-features',
    categoryLabel: 'AI Features',
    question: 'Can AI reference uploaded documents?',
    answer:
      'Absolutely! Every AI response includes clickable citation cards linking directly to exact workspace files, page numbers, and transcript timestamps.',
  },

  // Documents
  {
    id: 'doc-1',
    category: 'documents',
    categoryLabel: 'Documents',
    question: 'Which file formats are supported?',
    answer:
      'MindMesh supports PDF, Markdown (.md), DOCX, Plain Text, Codebase files (.py, .ts, .json), spreadsheets, and exported Slack/Teams chat transcripts.',
  },
  {
    id: 'doc-2',
    category: 'documents',
    categoryLabel: 'Documents',
    question: 'Is there a file size limit?',
    answer:
      'Free plan workspaces support files up to 25 MB. Pro and Enterprise workspaces support files up to 500 MB per document with background chunking.',
  },
  {
    id: 'doc-3',
    category: 'documents',
    categoryLabel: 'Documents',
    question: 'Can I preview documents directly inside MindMesh?',
    answer:
      'Yes! MindMesh includes a built-in document preview overlay for inspecting PDFs, Markdown rendered text, code snippets, and meeting transcripts without leaving the application.',
  },

  // Workspaces
  {
    id: 'ws-1',
    category: 'workspaces',
    categoryLabel: 'Workspaces',
    question: 'Can I create multiple workspaces?',
    answer:
      'Yes! Free plans include 5 Workspaces, Pro plans include 25 Workspaces, and Enterprise plans offer unlimited workspaces for different departments (Engineering, Legal, Product, Marketing).',
  },
  {
    id: 'ws-2',
    category: 'workspaces',
    categoryLabel: 'Workspaces',
    question: 'How are organization workspaces separated?',
    answer:
      'Each workspace is strictly isolated with logical tenant boundaries, RBAC permission policies, and AES-256 field-level data encryption.',
  },

  // Security
  {
    id: 'sec-1',
    category: 'security',
    categoryLabel: 'Security',
    question: 'Is my organization data encrypted?',
    answer:
      'Yes. MindMesh enforces AES-256 encryption at rest, TLS 1.3 in transit, and SAML SSO integration (Google Workspace & Microsoft Entra ID).',
  },
  {
    id: 'sec-2',
    category: 'security',
    categoryLabel: 'Security',
    question: 'Does MindMesh support Role-Based Access Control (RBAC)?',
    answer:
      'Yes! Granular roles for Owner, Admin, Manager, Member, and Guest specify exact document editing, AI search, billing, and administration rights.',
  },
  {
    id: 'sec-3',
    category: 'security',
    categoryLabel: 'Security',
    question: 'Are we compliant with SOC2 and GDPR?',
    answer:
      'MindMesh is built to meet SOC 2 Type II controls, ISO 27001 standards, and GDPR & CCPA privacy requirements.',
  },

  // Pricing
  {
    id: 'pr-1',
    category: 'pricing',
    categoryLabel: 'Pricing',
    question: 'Is there a free plan?',
    answer:
      'Yes! The Free plan is free forever and includes 5 Workspaces, 50 Documents, 0.04s Vector Search, and AI Chat Assistant.',
  },
  {
    id: 'pr-2',
    category: 'pricing',
    categoryLabel: 'Pricing',
    question: 'Do you offer annual billing discounts?',
    answer:
      'Yes! Annual billing saves 20% on Pro workspace seats ($15/mo billed annually vs $19/mo monthly).',
  },

  // Enterprise
  {
    id: 'ent-1',
    category: 'enterprise',
    categoryLabel: 'Enterprise',
    question: 'Do you support Single Sign-On (SAML SSO)?',
    answer:
      'Yes! Enterprise plans support SAML 2.0 SSO via Okta, Google Workspace, and Microsoft Entra ID.',
  },
  {
    id: 'ent-2',
    category: 'enterprise',
    categoryLabel: 'Enterprise',
    question: 'Is there an Enterprise SLA guarantee?',
    answer:
      'Enterprise contracts include a 99.9% uptime SLA guarantee with 24/7 dedicated solutions engineering support.',
  },

  // Technical
  {
    id: 'tech-1',
    category: 'technical',
    categoryLabel: 'Technical',
    question: 'Which web browsers are supported?',
    answer:
      'MindMesh works on all modern evergreen browsers including Google Chrome, Apple Safari, Mozilla Firefox, and Microsoft Edge.',
  },
  {
    id: 'tech-2',
    category: 'technical',
    categoryLabel: 'Technical',
    question: 'Can I export my workspace data?',
    answer:
      'Yes! You can export your documents, Knowledge Graph nodes, decision logs, and audit records in JSON, Markdown, or CSV formats at any time.',
  },
];
