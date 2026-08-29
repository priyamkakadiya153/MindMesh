# AI Agent Architecture (Part 1 — Agent Framework, Agent Types, Tool Calling, Planning Engine & Multi-Agent Orchestration)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the AI Agent Architecture of MindMesh. MindMesh AI Agents operate as modular, stateless, single-responsibility workers. It specifies agent categories, execution lifecycles, tool registry calls, task decomposition, and orchestration frameworks.

---

## Specialized Agent Categories
The platform segregates AI work across distinct domain agents registered in the orchestrator:
* **Planning Agent**: Parses user intent and creates sequential execution graphs of subtasks (does not run business logic).
* **Knowledge Agent**: Coordinates semantic retrieval, context extraction, and validates citations.
* **Search Agent**: Manages hybrid search parameters, filters, and rankings.
* **Document Agent**: Processes file OCR translations, summaries, metadata extractions, and revisions.
* **Conversation Agent**: Extracts action items, summaries, and decisions from chat records.
* **Task Agent**: Tracks task assignments, priorities, and dependency structures.
* **Security & Validation Agents**: Enforces workspace ACL permissions and audits generated text for hallucinations before output.

---

## Tool Calling Architecture
Agents modify application state strictly by invoking registered tools:

```text
Agent Prompt -> Tool Selector -> Validate Permissions -> Execute Tool API -> Observational State -> Agent Reason
```

* **Tool Scopes**: Tools present typed parameters.
* **No Direct DB Access**: Agents cannot execute arbitrary raw SQL queries. They rely exclusively on tools to read and write database values, maintaining validation constraints.

---

## Planning Engine & Orchestration
* **Task Decomposition**: Complex queries are split into sequential or parallel steps (e.g. "Summarize Project Alpha" splits into documents retrieval, message extractions, merging summaries, validation, and output formatting).
* **Parallel Execution**: Independent tasks run concurrently (e.g. pulling workspace messages and file OCR chunks in parallel) to reduce latency.
* **Failure Recovery**: The orchestrator retries failed tasks, falls back to alternative agent strategies, and notifies users gracefully.

---

## Target Performance Benchmarks (P95)
* **Task Planning**: < 100 ms
* **Agent Selection**: < 20 ms
* **Tool Invocation Checks**: < 20 ms
* **Knowledge Retrieval**: < 500 ms
* **Total Multi-Agent Coordination**: < 2 seconds (excluding LLM API latency)
