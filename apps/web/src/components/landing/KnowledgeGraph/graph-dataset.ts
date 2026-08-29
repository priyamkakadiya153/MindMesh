export type NodeType =
  | 'document'
  | 'project'
  | 'conversation'
  | 'person'
  | 'task'
  | 'meeting'
  | 'decision'
  | 'ai-agent';

export interface GraphNode {
  id: string;
  title: string;
  type: NodeType;
  x: number; // percentage 0 - 100
  y: number; // percentage 0 - 100
  badge: string;
  workspace: string;
  summary: string;
  connectedIds: string[];
  stats: {
    projects: number;
    conversations: number;
    meetings: number;
    tasks: number;
    people: number;
  };
}

export interface GraphEdge {
  from: string;
  to: string;
}

export const GRAPH_NODES: GraphNode[] = [
  {
    id: 'doc-1',
    title: 'Enterprise Security Policy',
    type: 'document',
    x: 50,
    y: 48,
    badge: 'Core Policy',
    workspace: 'Legal & Security',
    summary:
      'Central security policy mandating AES-256 encryption at rest, TLS 1.3 in transit, and RBAC tenant isolation across all enterprise workspaces.',
    connectedIds: ['proj-1', 'chat-1', 'person-1', 'task-1', 'meet-1', 'dec-1', 'ai-1'],
    stats: { projects: 4, conversations: 12, meetings: 3, tasks: 8, people: 5 },
  },
  {
    id: 'proj-1',
    title: 'Project Atlas',
    type: 'project',
    x: 24,
    y: 28,
    badge: 'In Progress',
    workspace: 'Engineering R&D',
    summary:
      'High-throughput vector indexing and organizational memory pipeline targeting 0.04s semantic retrieval SLA.',
    connectedIds: ['doc-1', 'task-1', 'ai-1', 'meet-1'],
    stats: { projects: 1, conversations: 8, meetings: 4, tasks: 12, people: 6 },
  },
  {
    id: 'chat-1',
    title: '#security-ops Channel',
    type: 'conversation',
    x: 76,
    y: 28,
    badge: 'Active Channel',
    workspace: 'Security Ops',
    summary:
      'Discussion thread covering SOC2 Type II audit readiness, tenant boundary verification, and single-device token revocation APIs.',
    connectedIds: ['doc-1', 'person-1', 'doc-2'],
    stats: { projects: 2, conversations: 15, meetings: 2, tasks: 4, people: 8 },
  },
  {
    id: 'person-1',
    title: 'Sarah (General Counsel)',
    type: 'person',
    x: 80,
    y: 72,
    badge: 'Owner',
    workspace: 'Legal & Compliance',
    summary:
      'Lead author for vendor master services agreements and enterprise data privacy addendums.',
    connectedIds: ['doc-1', 'chat-1', 'dec-1'],
    stats: { projects: 3, conversations: 24, meetings: 5, tasks: 6, people: 12 },
  },
  {
    id: 'task-1',
    title: 'Enforce AES-256 Encryption',
    type: 'task',
    x: 20,
    y: 72,
    badge: 'Task Priority #1',
    workspace: 'Engineering R&D',
    summary:
      'Implement zero-downtime database field-level encryption for all indexed workspace document chunks.',
    connectedIds: ['doc-1', 'proj-1', 'task-2'],
    stats: { projects: 2, conversations: 4, meetings: 2, tasks: 1, people: 3 },
  },
  {
    id: 'meet-1',
    title: 'Q3 Architecture Sync',
    type: 'meeting',
    x: 50,
    y: 18,
    badge: 'Meeting Transcript',
    workspace: 'Engineering R&D',
    summary:
      'Executive sync approving 15-minute JWT access token duration and sliding refresh sessions.',
    connectedIds: ['doc-1', 'proj-1', 'dec-1', 'person-2'],
    stats: { projects: 3, conversations: 6, meetings: 1, tasks: 5, people: 7 },
  },
  {
    id: 'dec-1',
    title: 'Decision #42: JWT Sliding Refresh',
    type: 'decision',
    x: 50,
    y: 82,
    badge: 'Extracted Decision',
    workspace: 'Security Ops',
    summary:
      'Approved 30-day sliding refresh token model with instant single-device session revocation endpoints.',
    connectedIds: ['doc-1', 'meet-1', 'person-1'],
    stats: { projects: 2, conversations: 9, meetings: 3, tasks: 4, people: 4 },
  },
  {
    id: 'ai-1',
    title: 'Vector Graph RAG Indexer',
    type: 'ai-agent',
    x: 32,
    y: 52,
    badge: 'AI Engine',
    workspace: 'System AI',
    summary:
      'Continuous background worker building semantic embeddings and knowledge node relationships.',
    connectedIds: ['doc-1', 'proj-1', 'proj-2'],
    stats: { projects: 5, conversations: 30, meetings: 10, tasks: 20, people: 15 },
  },
  {
    id: 'doc-2',
    title: 'SOC2 Type II Audit Report',
    type: 'document',
    x: 72,
    y: 50,
    badge: 'Audit PDF',
    workspace: 'Security Ops',
    summary:
      'Independent auditor evaluation confirming Security and Confidentiality Trust Services Criteria.',
    connectedIds: ['chat-1', 'doc-1', 'person-2'],
    stats: { projects: 2, conversations: 7, meetings: 2, tasks: 3, people: 4 },
  },
  {
    id: 'proj-2',
    title: 'MindMesh AI Engine v2',
    type: 'project',
    x: 14,
    y: 46,
    badge: 'In Planning',
    workspace: 'Product & Design',
    summary:
      'Next-generation hybrid sparse-dense vector engine with real-time Slack/Teams ingestion.',
    connectedIds: ['ai-1', 'proj-1'],
    stats: { projects: 1, conversations: 5, meetings: 3, tasks: 8, people: 5 },
  },
  {
    id: 'person-2',
    title: 'Alex (CTO)',
    type: 'person',
    x: 86,
    y: 46,
    badge: 'Executive',
    workspace: 'Leadership',
    summary:
      'Technical executive overseeing security compliance, platform architecture, and AI roadmap.',
    connectedIds: ['meet-1', 'doc-2'],
    stats: { projects: 8, conversations: 40, meetings: 15, tasks: 10, people: 20 },
  },
  {
    id: 'task-2',
    title: 'Audit RBAC Permissions',
    type: 'task',
    x: 36,
    y: 84,
    badge: 'Task Priority #2',
    workspace: 'Security Ops',
    summary:
      'Verify role isolation between Workspace Owners, Admins, Members, and Guest reviewers.',
    connectedIds: ['task-1', 'doc-1'],
    stats: { projects: 1, conversations: 3, meetings: 1, tasks: 1, people: 2 },
  },
];

export const GRAPH_EDGES: GraphEdge[] = [
  { from: 'doc-1', to: 'proj-1' },
  { from: 'doc-1', to: 'chat-1' },
  { from: 'doc-1', to: 'person-1' },
  { from: 'doc-1', to: 'task-1' },
  { from: 'doc-1', to: 'meet-1' },
  { from: 'doc-1', to: 'dec-1' },
  { from: 'doc-1', to: 'ai-1' },
  { from: 'chat-1', to: 'doc-2' },
  { from: 'proj-1', to: 'ai-1' },
  { from: 'proj-1', to: 'task-1' },
  { from: 'meet-1', to: 'dec-1' },
  { from: 'meet-1', to: 'person-2' },
  { from: 'task-1', to: 'task-2' },
  { from: 'proj-2', to: 'ai-1' },
  { from: 'person-2', to: 'doc-2' },
];
