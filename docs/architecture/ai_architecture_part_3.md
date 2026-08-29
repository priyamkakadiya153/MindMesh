# AI Architecture (Part 3 — Prompt Engineering, Memory Engine, AI Workflows & Multi-Provider Orchestration)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines how MindMesh constructs prompts, manages AI memory, orchestrates AI workflows, routes requests across multiple LLM providers, validates responses, and minimizes hallucinations.

---

## Prompt Template Design
Prompts must never be concatenated manually or hardcoded inside business functions. Prompt templates are kept modular and versioned separately from core application logic.

Every generated prompt follows this structural hierarchy:
1. **System Instructions**: Primary behavior instructions.
2. **User Context**: Tone preferences and parameters.
3. **Workspace Context**: Common workspace standards and configurations.
4. **Project Context**: Relevant active project milestones.
5. **Retrieved Knowledge**: The output from the hybrid context retrieval pipeline.
6. **Conversation History**: Recent contextual messages.
7. **Current Question**: Direct input query.
8. **Output Requirements**: Strict output guidelines (JSON schemas, citations rules).

---

## Hierarchical Memory Engine
Memory is partitioned by scoping boundaries to ensure user data isolation:
* **Global Memory**: Read-only product guidelines and system instructions.
* **Workspace Memory**: Workspace decisions, documents, and reference parameters.
* **Project Memory**: Active project specifications, milestones, and meeting summaries.
* **Conversation Memory**: Short-term recent message contexts.
* **User Memory**: Private individual configuration preferences (cannot leak across users).

*Retrieval Prioritization*: 1. Current Conversation -> 2. Current Project -> 3. Workspace -> 4. User -> 5. Global.

---

## AI Provider Routing & Failovers
* **Routing Strategy**: Simple summaries or lightweight extraction jobs map to efficient models, while complex cross-document reasoning maps to premium reasoning models.
* **Sensitive Data Routing**: Local or on-premise models are prioritized when workspace parameters require offline/private processing.
* **Failover Protocol**: Primary provider timeouts or errors trigger automatic retries before falling back to secondary providers.

---

## Guardrails & Output Validation
Before and after model inference, the guardrail engine enforces safety checks:
* **In-Boundary Check**: Detects prompt injection patterns and restricts context inputs.
* **Out-Boundary Check**: Validates that citations exist, JSON formats are correct, and no hallucinated text is returned.
