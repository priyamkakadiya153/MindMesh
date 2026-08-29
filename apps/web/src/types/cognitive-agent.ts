/**
 * MindMesh — Cognitive Agent TypeScript Type Definitions (CA-01)
 * Formal domain contract interfaces matching backend CognitiveAgent models.
 */

export type CognitiveAgentStatus = 'ACTIVE' | 'PAUSED' | 'DISABLED' | 'ARCHIVED';

export type CognitiveAgentType =
  | 'KNOWLEDGE_SYNTHESIZER'
  | 'DISCUSSION_ANALYZER'
  | 'DOCUMENT_PARSER'
  | 'PROJECT_MONITOR'
  | 'CUSTOM';

export type CognitiveAgentScopeType =
  | 'WORKSPACE'
  | 'PROJECT'
  | 'DOCUMENT'
  | 'CONVERSATION'
  | 'CHANNEL'
  | 'SELECTED_KNOWLEDGE';

export type CognitiveAgentTriggerType =
  | 'MANUAL'
  | 'CONVERSATION_EVENT'
  | 'DOCUMENT_EVENT'
  | 'PROJECT_EVENT'
  | 'SCHEDULE';

export type CognitiveAgentOutputType =
  | 'INSIGHT'
  | 'SUMMARY'
  | 'RECOMMENDATION'
  | 'ACTION_CANDIDATE';

export type CognitiveAgentExecutionStatus =
  | 'QUEUED'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export interface CognitiveAgentScope {
  scope_type: CognitiveAgentScopeType;
  workspace_id?: string;
  project_id?: string;
  document_ids?: string[];
  conversation_ids?: string[];
  channel_ids?: string[];
  restricted_knowledge_keys?: string[];
}

export interface CognitiveAgentTrigger {
  trigger_type: CognitiveAgentTriggerType;
  event_pattern?: string;
  cron_expression?: string;
  enabled: boolean;
}

export interface CognitiveAgentProvenance {
  source_type: string;
  source_id: string;
  source_reference?: string;
  confidence_score: number;
}

export interface CognitiveAgentOutput {
  output_id?: string;
  agent_id: string;
  organization_id: string;
  workspace_id?: string;
  output_type: CognitiveAgentOutputType;
  title: string;
  body: string;
  metadata?: Record<string, any>;
  provenance: CognitiveAgentProvenance[];
  created_at: string;
  candidate_type?: string;
  assignee_id?: string;
  assignee_name?: string;
  deadline?: string;
}

export interface CognitiveAgentExecution {
  execution_id: string;
  agent_id: string;
  organization_id: string;
  workspace_id?: string;
  trigger_source: CognitiveAgentTriggerType;
  started_at: string;
  completed_at?: string;
  input_context?: Record<string, any>;
  outputs?: CognitiveAgentOutput[];
  action_candidates_generated: number;
  status: CognitiveAgentExecutionStatus;
  error_message?: string;
}

export interface CognitiveAgent {
  id: string;
  organization_id: string;
  workspace_id?: string;
  owner_user_id: string;
  name: string;
  description: string;
  agent_type: CognitiveAgentType;
  instructions: string;
  status: CognitiveAgentStatus;
  enabled: boolean;
  knowledge_scope: CognitiveAgentScope;
  triggers: CognitiveAgentTrigger[];
  created_at: string;
  updated_at: string;
  last_execution?: CognitiveAgentExecution | null;
}

export interface CognitiveAgentCreate {
  name: string;
  description?: string;
  agent_type?: CognitiveAgentType;
  instructions: string;
  status?: CognitiveAgentStatus;
  enabled?: boolean;
  workspace_id?: string;
  knowledge_scope?: CognitiveAgentScope;
  triggers?: CognitiveAgentTrigger[];
}

export interface CognitiveAgentUpdate {
  name?: string;
  description?: string;
  agent_type?: CognitiveAgentType;
  instructions?: string;
  status?: CognitiveAgentStatus;
  enabled?: boolean;
  workspace_id?: string;
  knowledge_scope?: CognitiveAgentScope;
  triggers?: CognitiveAgentTrigger[];
}

export interface CognitiveAgentTriggerRecord {
  id: string;
  agent_id: string;
  organization_id: string;
  workspace_id?: string;
  trigger_type: 'SCHEDULE' | 'EVENT' | 'MANUAL';
  status: 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'FAILED' | 'DISABLED';
  schedule_type?: 'ONE_TIME' | 'DAILY' | 'WEEKLY' | 'WEEKDAYS' | 'MONTHLY';
  time_str?: string;
  day_of_week?: string;
  timezone: string;
  event_type?: string;
  event_filters?: any;
  next_run_at?: string | null;
  last_run_at?: string | null;
  last_execution_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CognitiveAgentProvenanceSource {
  source_type: 'document' | 'conversation' | 'project' | 'task' | 'decision' | string;
  source_id: string;
  title: string;
  filename?: string;
  mime_type?: string;
  conversation_id?: string;
  message_id?: string;
  message_text?: string;
  project_id?: string;
  is_available?: boolean;
  is_stale?: boolean;
  status_message?: string | null;
  stale_message?: string | null;
  retrieved_at?: string | null;
}

export interface CognitiveAgentOutputRecord {
  id: string;
  execution_id: string;
  agent_id: string;
  organization_id: string;
  workspace_id?: string;
  output_type: CognitiveAgentOutputType | string;
  title: string;
  body: string;
  candidate_type?: string | null;
  structured_payload?: any;
  provenance?: CognitiveAgentProvenanceSource[];
  created_at: string;
}



