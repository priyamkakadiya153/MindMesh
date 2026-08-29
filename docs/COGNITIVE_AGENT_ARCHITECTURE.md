# MindMesh — Cognitive Agent Architecture & Domain Contract Specification

**Document Version:** 1.0  
**Phase:** CA-01 (Cognitive Agent Foundation & Architecture)  
**Status:** Approved Architectural Contract  

---

## 1. Executive Summary & Core Product Definition

In MindMesh, a **Cognitive Agent** is an intelligent, specialized knowledge worker designed to continuously monitor, reason over, analyze, and synthesize organizational context across chats, documents, files, and project structures.

### Key Characteristics of a Cognitive Agent:
1. **Clearly Defined Responsibility**: Focuses on a specific task domain (e.g., discussion summarization, document ingestion mapping, project milestone tracking).
2. **Controlled Knowledge Scope**: Restricts data access strictly to authorized Workspaces, Projects, Documents, or Channels based on owner permissions.
3. **Structured Outputs**: Produces defined output types (`INSIGHT`, `SUMMARY`, `RECOMMENDATION`, or `ACTION_CANDIDATE`).
4. **Execution History & Traceability**: Tracks full provenance back to source messages, documents, or decisions.
5. **Security & Permission Boundaries**: Respects user RBAC and Zero-Trust isolation. Data across Organizations or Workspaces is strictly segregated.

---

## 2. Integration with MindMesh Automation Architecture (`AUTO-01` .. `AUTO-10`)

Cognitive Agents **do not create a secondary automation framework**. The existing MindMesh intent detection, action candidate, action inbox, confirmation, and audit system remains authoritative.

### High-Level Architectural Flow:

```
+-------------------------------------------------------------------------+
|    Knowledge Sources (Conversations / Documents / Files / Projects)     |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                            Cognitive Agent                              |
|           - Analyzes knowledge within scope                             |
|           - Reasons using System Prompt & Goal Instructions             |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                             Agent Output                                |
|        (1. INSIGHT | 2. SUMMARY | 3. RECOMMENDATION | 4. ACTION_CANDIDATE) |
+-------------------------------------------------------------------------+
                                    |
            +-----------------------+-----------------------+
            | (Insight/Summary/Rec)                         | (Action Candidate)
            v                                               v
+-----------------------+                       +-----------------------+
|  Knowledge Workspace  |                       |  MindMesh Action Inbox |
|  & Dashboard Display  |                       |  (Candidate Status:   |
|                       |                       |   DETECTED)           |
+-----------------------+                       +-----------------------+
                                                            |
                                                            v
                                                +-----------------------+
                                                |     AUTO-06 Policy    |
                                                | Confirmation & Safety |
                                                |  (User Accepts Action)|
                                                +-----------------------+
                                                            |
                                                            v
                                                +-----------------------+
                                                | Execution Pipeline    |
                                                | (AUTO-02 / AUTO-04 /  |
                                                |  AUTO-03 Execution)   |
                                                +-----------------------+
                                                            |
                                                            v
                                                +-----------------------+
                                                |      AUTO-07 Audit    |
                                                |  Trail & Action Memory|
                                                +-----------------------+
```

### CRITICAL GUARANTEE: Zero Unsanctioned Autonomous Actions
A Cognitive Agent must **NEVER** silently:
- Create a task or reminder
- Send a direct message or channel post
- Schedule an automation
- Modify or delete existing user data
- Perform destructive operations

Any execution proposal must be emitted as an `ACTION_CANDIDATE` and submitted to the **Action Inbox**, where the user must review and approve it via `AUTO-06`.

---

## 3. Cognitive Agent Domain Entity Contract

The domain contract defines the conceptual attributes of an Agent in MindMesh:

```typescript
interface CognitiveAgent {
  id: string; // UUID
  organization_id: string; // UUID
  workspace_id?: string; // UUID (Optional workspace scoping)
  owner_user_id: string; // UUID of owner / creator
  name: string;
  description: string;
  agent_type: CognitiveAgentType;
  instructions: string; // System prompt / operational guidelines
  status: CognitiveAgentStatus; // ACTIVE | PAUSED | DISABLED | ARCHIVED
  enabled: boolean;
  knowledge_scope: CognitiveAgentScope;
  triggers: CognitiveAgentTrigger[];
  created_at: string; // ISO 8601 UTC
  updated_at: string; // ISO 8601 UTC
}
```

### Agent Status Enum (`CognitiveAgentStatus`):
- `ACTIVE`: Fully operational and responding to triggers.
- `PAUSED`: Temporarily inactive; preserves configuration but skips triggers.
- `DISABLED`: Deactivated due to governance, permissions, or system administrative policy.
- `ARCHIVED`: Soft-deleted / historical record preserved for audit traceability.

### Agent Types (`CognitiveAgentType`):
- `KNOWLEDGE_SYNTHESIZER`: Summarizes discussions, decisions, and documentation.
- `DISCUSSION_ANALYZER`: Extracts action items, decisions, and commitments from chats.
- `DOCUMENT_PARSER`: Extracts structured metadata and embeddings from uploaded files.
- `PROJECT_MONITOR`: Tracks milestones, approaching deadlines, and risks.
- `CUSTOM`: Extensible specialist agent defined by user instructions.

---

## 4. Execution Lifecycle Contract

Every Cognitive Agent execution run is strictly traceable:

```
[ QUEUED ]  --->  [ RUNNING ]  --->  [ COMPLETED ]
                      |
                      +----------->  [ FAILED ]
                      |
[ QUEUED / RUNNING ]  ---------->  [ CANCELLED ]
```

### Execution Model Attributes (`CognitiveAgentExecution`):
- `execution_id`: Unique identifier for the run.
- `agent_id`: Target agent ID.
- `organization_id` & `workspace_id`: Tenant scope.
- `trigger_source`: Event source (`MANUAL`, `CONVERSATION_EVENT`, `DOCUMENT_EVENT`, `PROJECT_EVENT`, `SCHEDULE`).
- `started_at` & `completed_at`: Microsecond precision timestamps.
- `input_context`: Data references passed to the agent.
- `output_summary`: Summary of produced insights, recommendations, or candidates.
- `status`: Execution status (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`).
- `error_message`: Full error detail if `status === FAILED`.

---

## 5. Knowledge Scope & Permission Contract

Agents operate strictly under **Least-Privilege Authorization**:
1. **Scope Boundaries**:
   - `WORKSPACE`: Knowledge in a specific workspace.
   - `PROJECT`: Knowledge bound to a project.
   - `DOCUMENT`: Specific document or folder.
   - `CONVERSATION`: Specific chat thread or channel.
   - `SELECTED_KNOWLEDGE`: Explicitly enumerated document/item list.
2. **Permission Boundary**: An agent's knowledge access cannot exceed the authorization of its `owner_user_id`.
3. **Data Isolation**: Multi-tenant boundaries (`organization_id` and `workspace_id`) are enforced at SQL/Vector query time. Cross-tenant leakage is strictly impossible.

---

## 6. Trigger Contract

Supported trigger modalities:
- `MANUAL`: Triggered explicitly by user request via API or UI.
- `CONVERSATION_EVENT`: Fired on message post, thread creation, or mention.
- `DOCUMENT_EVENT`: Fired on file upload, edit, or chunking completion.
- `PROJECT_EVENT`: Fired on project state change or milestone update.
- `SCHEDULE`: Recurring execution using the existing scheduling infrastructure. **No second scheduler will be built.**

---

## 7. Output & Action Integration Contract

Cognitive Agent outputs are typed into 4 distinct categories:

```typescript
type CognitiveAgentOutputType = 'INSIGHT' | 'SUMMARY' | 'RECOMMENDATION' | 'ACTION_CANDIDATE';
```

### Output Structures:
1. `INSIGHT`: Highlighted observation (e.g., "3 project tasks are approaching deadlines this Friday").
2. `SUMMARY`: Synthesized knowledge (e.g., "Weekly engineering discussion produced 4 key decisions").
3. `RECOMMENDATION`: Suggested action or focus area (e.g., "API documentation has no assigned reviewer").
4. `ACTION_CANDIDATE`: Proposed system action. MUST be automatically converted into an `ActionCandidate` and dispatched to the **Action Inbox** (`/api/v1/actions/candidates`).

---

## 8. Provenance & Explanability Requirement

Every output must answer: *"What specific information caused the agent to produce this result?"*

### Provenance Attributes (`CognitiveAgentProvenance`):
- `source_type`: `CONVERSATION` | `DOCUMENT` | `PROJECT` | `TASK` | `DECISION`
- `source_id`: Specific UUID of the source entity
- `source_reference`: Excerpt snippet or line location
- `confidence_score`: Floating point score `0.0 - 1.0`

---

## 9. Security Guardrails & Prompt Injection Protection

1. **Strict Data Scoping**: Retrieved context (messages, files) is treated strictly as **DATA**, never as control instructions.
2. **Instruction Protection**: User text or retrieved knowledge cannot alter the agent's identity, permission set, available tools, or safety rules.
3. **Action Safety**: No action execution without `AUTO-06` confirmation.

---

## 10. Summary of Architectural Guarantees

| Requirement | Contract Guarantee |
|---|---|
| **Autonomous Action** | Prohibited. Must pass through `ActionCandidate` -> `ActionInbox` -> `AUTO-06`. |
| **Multi-Tenancy** | Strictly enforced via `organization_id` & `workspace_id`. |
| **Scheduler** | Reuses existing scheduling infrastructure. |
| **Auditability** | All actions logged in `AUTO-07` action memory & audit trail. |
| **Extensibility** | Agent types and trigger definitions use open, extensible enums. |
