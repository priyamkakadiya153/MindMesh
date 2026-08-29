# AI Agent Architecture (Part 2 — Memory Architecture, Reflection, Self-Evaluation, Guardrails, Human-in-the-Loop & Agent Governance)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence Platform

---

## Purpose
This document defines how AI Agents in MindMesh remember, learn, validate, govern themselves, and remain safe. It covers the hierarchical memory system, self-evaluation reflection loops, validation steps, Human-in-the-loop (HITL) overrides, and data protection policies.

---

## Hierarchical Memory Systems
MindMesh segments agent state memories across six distinct scopes to prevent context pollution:
1. **Working Memory**: Temporary operational state containing intermediate tool outputs. Expires immediately after execution.
2. **Conversation Memory**: Tracks thread logs (previous Q&A nodes) to support context chats.
3. **Workspace Memory**: Retains workspace terms and document histories. *Isolated strictly to the workspace context.*
4. **User Memory**: Persists user preferences and language selections.
5. **Episodic Memory**: Records history of successful tool runs to optimize future plans.
6. **Semantic Memory**: Maps concepts, facts, and relations retrieved from the Knowledge Graph.

---

## Reflection & Self-Evaluation Engines
* **Self-Reflection Check**: Before returning a response draft, the agent evaluates its results, verifying citation alignments, check scopes, and fact bases.
* **Confidence Scoring**: Responses calculate a confidence coefficient (`0.0` to `1.0`) derived from source relevance and model agreement. Low-confidence responses route to validation sub-pipelines or prompt the user for clarification.

---

## Output Validation & HITL Gateways

### 1. Validation Pipeline
```text
Draft Response -> Citation Checks -> Fact Audit -> Guardrail Policy Check -> ACL Verification -> Final Response
```

### 2. Human-in-the-Loop (HITL) Gateways
* Certain sensitive actions require explicit human validation:
  * Bulk files or messages deletions.
  * External third-party integrations data exports.
  * Workflow auto-notifications dispatching.
  * Multi-step integrations.

---

## Policy & Cost Governance
* **Sensitive Data Protection**: Policies scan payloads to mask password tokens, credential files, or personal information.
* **Cost Allocations**: Limits tokens budgets and tracks provider billing (Gemini, Claude, local models) per user or workspace.
