import re
import logging
from typing import List, Dict, Any, Optional

from app.ai.intent.engine import IntentEngine
from app.ai.intent.models import IntentType

from .models import RequestIntent, RequestType, CapabilityType, RequestUnderstanding
from .context_resolver import ContextResolver
from app.actions.types import ActionStatus
from app.actions.classifier import ActionClassifier
from app.actions.types import ActionIntentType

logger = logging.getLogger(__name__)

class SemanticUnderstandingEngine:
    """
    Universal MindMesh Semantic Query Understanding Engine.
    
    Transforms arbitrary natural language into a rich RequestUnderstanding representation
    to drive domain-specific execution capability selection.
    """

    GREETING_WORDS = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"}
    THANKS_WORDS = {"thanks", "thank you", "thanks!", "thank you!", "okay", "ok", "great", "got it"}

    GENERAL_KNOWLEDGE_CONCEPTS = [
        "api", "rest", "postgresql", "postgres", "vector database", "vector search",
        "graphql", "http", "tcp", "docker", "kubernetes", "react", "python",
        "recursion", "caching", "addition", "subtraction", "multiplication", "division",
        "polymorphism", "algorithm", "data structure"
    ]

    @classmethod
    def parse_request(
        cls,
        query: str,
        history: Optional[List[Dict[str, Any]]] = None,
        pending_action: Optional[Dict[str, Any]] = None
    ) -> RequestUnderstanding:
        clean_query = query.strip()
        q_lower = clean_query.lower()

        # 1. Resolve Conversation References & Pending Action Context
        refs = ContextResolver.resolve_references(clean_query, history, pending_action)
        if refs.get("pending_fill"):
            fill = refs["pending_fill"]
            return RequestUnderstanding(
                intent=RequestIntent.CREATE_TASK,
                request_type=RequestType.ACTION,
                confidence=1.0,
                entities={"title": fill["value"]},
                required_capability=CapabilityType.ACTION_WORKFLOW,
                response_mode="ACTION_PROPOSAL",
                raw_query=clean_query
            )

        # 2. Ambiguous Short Inputs (e.g. "Can you add something?", "Can you add?")
        if q_lower in ["can you add something", "can you add something?", "can you add", "can you add?", "add something"]:
            return RequestUnderstanding(
                intent=RequestIntent.UNKNOWN,
                request_type=RequestType.CONVERSATIONAL,
                confidence=0.9,
                required_capability=CapabilityType.CLARIFY,
                ambiguity="User asked to add something without specifying the item or item type.",
                response_mode="CLARIFICATION_PROMPT",
                raw_query=clean_query
            )

        # 3. Pure Greetings & Thanks
        clean_punct = q_lower.strip("!?. ")
        if clean_punct in cls.GREETING_WORDS:
            return RequestUnderstanding(
                intent=RequestIntent.GREETING,
                request_type=RequestType.CONVERSATIONAL,
                confidence=1.0,
                required_capability=CapabilityType.CONVERSATIONAL_SMALLTALK,
                response_mode="DIRECT_ANSWER",
                raw_query=clean_query
            )
        elif clean_punct in cls.THANKS_WORDS:
            return RequestUnderstanding(
                intent=RequestIntent.THANKS,
                request_type=RequestType.CONVERSATIONAL,
                confidence=1.0,
                required_capability=CapabilityType.CONVERSATIONAL_SMALLTALK,
                response_mode="DIRECT_ANSWER",
                raw_query=clean_query
            )

        # 4. Math & Direct General Knowledge
        math_match = re.search(r'^\s*(what is|calculate|compute|how much is|can you add|add)?\s*(\d+\s*[\+\-\*\/\,\s]+\s*\d+|\d+\s+(plus|minus|times|divided by)\s+\d+)\s*\??$', clean_query, re.IGNORECASE)
        if math_match:
            return RequestUnderstanding(
                intent=RequestIntent.GENERAL_KNOWLEDGE,
                request_type=RequestType.GENERAL_KNOWLEDGE,
                confidence=1.0,
                entities={"math_expr": math_match.group(2).strip()},
                required_capability=CapabilityType.GENERAL_LLM,
                response_mode="DIRECT_ANSWER",
                raw_query=clean_query
            )

        # General Knowledge terms (e.g. "What is an API?", "What is REST?", "Explain PostgreSQL", "What's addition?")
        is_gen_query = False
        workspace_exclusions = ["pdf", "file", "document", "report", "discussion", "workspace", "my", "our", "project", "task", "decision", "say about", "say regarding", ".pdf", ".docx", ".txt", ".md"]
        if any(q_lower.startswith(prefix) for prefix in ["what is an ", "what is a ", "what is ", "explain ", "what does ", "why is ", "what's "]):
            topic_part = re.sub(r'^(what is an|what is a|what is|explain|what does|why is|what\'s)\s+', '', q_lower).strip("? ")
            if not any(w in q_lower for w in workspace_exclusions):
                if any(re.search(r'\b' + re.escape(concept) + r'\b', topic_part) for concept in cls.GENERAL_KNOWLEDGE_CONCEPTS):
                    is_gen_query = True

        if is_gen_query:
            return RequestUnderstanding(
                intent=RequestIntent.GENERAL_KNOWLEDGE,
                request_type=RequestType.GENERAL_KNOWLEDGE,
                confidence=1.0,
                rewritten_query=clean_query,
                required_capability=CapabilityType.GENERAL_LLM,
                response_mode="DIRECT_ANSWER",
                raw_query=clean_query
            )

        # 5. Preserve safe mutating actions, reminders, and DMs through the
        # existing proposal / clarification workflow.
        action_proposal = ActionClassifier.classify(clean_query, workspace_id=None, user_id=None, resolved_context=refs)
        if action_proposal and not action_proposal.parameters.get("is_history_query"):
            followup_goal = refs.get("followup_goal") or {}
            if followup_goal and action_proposal.intent_type == ActionIntentType.CREATE_TASK:
                title = action_proposal.parameters.get("title", "") or ""
                generic_title_tokens = {"", "that", "this", "it", "thing", "item", "something", "that on my list", "this on my list", "it on my list"}
                if title.strip().lower() in generic_title_tokens or title.strip().lower().startswith("that "):
                    action_proposal.parameters["title"] = followup_goal.get("title", title)
                    if followup_goal.get("due_date_str") and not action_proposal.parameters.get("due_date_str"):
                        action_proposal.parameters["due_date_str"] = followup_goal.get("due_date_str")
                    action_proposal.title = f"Create Task: {action_proposal.parameters['title']}"
                    action_proposal.description = f"Action proposal to create task '{action_proposal.parameters['title']}'."
                    action_proposal.status = ActionStatus.READY_FOR_CONFIRMATION

            req_intent = RequestIntent.UNKNOWN
            try:
                req_intent = RequestIntent(action_proposal.intent_type.value)
            except ValueError:
                req_intent = RequestIntent.CREATE_TASK

            if action_proposal.status == ActionStatus.NEEDS_CLARIFICATION:
                missing_params = ["title"] if action_proposal.intent_type.value == "CREATE_TASK" else ["time_str"]
                return RequestUnderstanding(
                    intent=req_intent,
                    request_type=RequestType.ACTION,
                    confidence=1.0,
                    rewritten_query=clean_query,
                    required_capability=CapabilityType.ACTION_WORKFLOW,
                    missing_information=missing_params,
                    response_mode="CLARIFICATION_PROMPT",
                    raw_query=clean_query
                )

            return RequestUnderstanding(
                intent=req_intent,
                request_type=RequestType.ACTION,
                confidence=1.0,
                rewritten_query=clean_query,
                entities=action_proposal.parameters,
                conversation_refs=refs,
                required_capability=CapabilityType.ACTION_WORKFLOW,
                response_mode="ACTION_PROPOSAL",
                raw_query=clean_query
            )

        # 6. Explicit Domain Queries (Tasks, Reminders, Automations, DMs, Decisions, Graph, Metadata)
        # Reminder Queries (read-only)
        if any(phrase in q_lower for phrase in ["what reminders do i have", "what reminders do we have", "my reminders", "show reminders", "show my reminders", "list reminders"]):
            return RequestUnderstanding(
                intent=RequestIntent.REMINDER_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.TASK_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Automation Queries (read-only)
        if any(phrase in q_lower for phrase in ["what automations do i have", "what automations do we have", "my automations", "show automations", "show my automations", "list automations"]):
            return RequestUnderstanding(
                intent=RequestIntent.AUTOMATION_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.TASK_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Direct Message Queries (read-only)
        if any(phrase in q_lower for phrase in ["what messages did i receive", "what messages do i have", "my messages", "show messages", "show my dms"]):
            return RequestUnderstanding(
                intent=RequestIntent.DM_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.TASK_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Extraction Queries (e.g., "Extract all tasks, responsibilities, deadlines, and decisions...")
        if "extract " in q_lower or "extraction" in q_lower or ("extract" in q_lower and ("task" in q_lower or "decision" in q_lower or "deadline" in q_lower or "responsibilit" in q_lower)):
            return RequestUnderstanding(
                intent=RequestIntent.EXTRACTION_REQUEST,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.TASK_EXTRACTION,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Summary Queries (e.g., "Summarize this project discussion", "Summarize the conversation")
        if any(phrase in q_lower for phrase in ["summarize", "summary of", "recap"]):
            return RequestUnderstanding(
                intent=RequestIntent.SUMMARY_REQUEST,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.DISCUSSION_SUMMARY,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Task Queries (read-only list of current tasks)
        if any(phrase in q_lower for phrase in ["what tasks do i have", "what tasks do we have", "my tasks", "which tasks are pending", "which tasks are still pending", "tell me what tasks are pending", "what tasks are pending", "anything overdue", "show pending tasks", "pending tasks", "who is working on", "who is responsible"]) and not any(verb in q_lower for verb in ["add", "put", "create", "make", "assign", "set", "remind", "tell", "every", "extract", "summar"]):
            return RequestUnderstanding(
                intent=RequestIntent.TASK_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.TASK_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Decision & Architectural Queries
        if any(phrase in q_lower for phrase in ["what did we decide", "decided about", "decision about", "what were the decisions", "what decisions", "architectural decisions", "architecture decisions", "decisions made"]):
            return RequestUnderstanding(
                intent=RequestIntent.DECISION_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.KNOWLEDGE_SYNTHESIS,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Knowledge Graph / Dependency Queries
        if any(phrase in q_lower for phrase in ["why is this task blocked", "why is that task blocked", "why is the deployment task blocked", "what does this project depend on", "why did this decision happen", "which task came from"]) or (("why is" in q_lower or "why are" in q_lower) and "blocked" in q_lower):
            return RequestUnderstanding(
                intent=RequestIntent.GRAPH_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.GRAPH_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Explicit Search Queries (e.g., "Find conversations about...", "Search messages for...")
        if any(phrase in q_lower for phrase in ["find conversation", "search conversation", "find discussions", "search discussions", "find message", "search message", "find threads"]):
            return RequestUnderstanding(
                intent=RequestIntent.CONVERSATION_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.CONVERSATION_SEARCH_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Shared Files Collaboration Queries (e.g., "What files did Priyam share with me?", "Who shared API.zip?", "Show files shared in Project Discussion")
        if any(phrase in q_lower for phrase in [
            "who shared", "what files did", "what files were shared", "files shared with me",
            "files shared by me", "files shared in", "shared files in", "show shared files",
            "list shared files", "files did"
        ]) or ("shared" in q_lower and any(w in q_lower for w in ["file", "files", "attachment", "attachments", "zip", "png", "jpg", "pdf"])):
            return RequestUnderstanding(
                intent=RequestIntent.SHARED_FILES_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.SHARED_FILES_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # 7. Semantic routing for natural-language requests via IntentEngine.
        intent_result = IntentEngine.understand_query(clean_query, conversation_history=history or [])
        rewritten_query = intent_result.rewritten_query or clean_query

        semantic_capability = None
        semantic_request_intent = RequestIntent.UNKNOWN
        semantic_request_type = RequestType.QUERY

        if intent_result.requires_clarification or intent_result.intent == IntentType.AMBIGUOUS:
            semantic_capability = CapabilityType.CLARIFY
            semantic_request_intent = RequestIntent.CLARIFICATION_RESPONSE
            semantic_request_type = RequestType.CLARIFICATION_RESPONSE
        elif intent_result.intent in {IntentType.GREETING, IntentType.THANKS}:
            semantic_capability = CapabilityType.CONVERSATIONAL_SMALLTALK
            semantic_request_intent = RequestIntent.GREETING if intent_result.intent == IntentType.GREETING else RequestIntent.THANKS
            semantic_request_type = RequestType.CONVERSATIONAL
        elif intent_result.intent == IntentType.GENERAL_KNOWLEDGE:
            semantic_capability = CapabilityType.GENERAL_LLM
            semantic_request_intent = RequestIntent.GENERAL_KNOWLEDGE
            semantic_request_type = RequestType.GENERAL_KNOWLEDGE
        elif intent_result.intent == IntentType.ACTION_REQUEST:
            semantic_capability = CapabilityType.ACTION_WORKFLOW
            semantic_request_intent = RequestIntent.UNKNOWN
            semantic_request_type = RequestType.ACTION
        elif any(phrase in q_lower for phrase in ["what did ai do", "what did you do for me", "what actions did ai", "ai actions today"]):
            semantic_capability = CapabilityType.ACTION_AUDIT_SERVICE
            semantic_request_intent = RequestIntent.ACTION_HISTORY_QUERY
        elif intent_result.intent == IntentType.EXTRACTION_REQUEST:
            semantic_capability = CapabilityType.TASK_EXTRACTION
            semantic_request_intent = RequestIntent.EXTRACTION_REQUEST
        elif intent_result.intent == IntentType.SUMMARY_REQUEST:
            semantic_capability = CapabilityType.DISCUSSION_SUMMARY
            semantic_request_intent = RequestIntent.SUMMARY_REQUEST
        elif intent_result.intent == IntentType.SEARCH_QUERY:
            semantic_capability = CapabilityType.CONVERSATION_SEARCH_SERVICE
            semantic_request_intent = RequestIntent.CONVERSATION_QUERY
        elif intent_result.intent == IntentType.COMPARISON_REQUEST:
            semantic_capability = CapabilityType.MULTI_DOC_COMPARE
            semantic_request_intent = RequestIntent.MULTI_DOC_COMPARE
        elif intent_result.intent == IntentType.TASK_QUERY:
            semantic_capability = CapabilityType.TASK_SERVICE
            semantic_request_intent = RequestIntent.TASK_QUERY
        elif intent_result.intent == IntentType.PROJECT_QUERY:
            semantic_capability = CapabilityType.KNOWLEDGE_SYNTHESIS
            semantic_request_intent = RequestIntent.PROJECT_QUERY
        elif intent_result.intent == IntentType.DECISION_QUERY:
            semantic_capability = CapabilityType.KNOWLEDGE_SYNTHESIS
            semantic_request_intent = RequestIntent.DECISION_QUERY
        elif intent_result.intent == IntentType.DOCUMENT_QUERY:
            semantic_capability = CapabilityType.DOCUMENT_RAG
            semantic_request_intent = RequestIntent.DOCUMENT_QUERY
        elif intent_result.intent == IntentType.CONVERSATION_QUERY:
            # Check if this is an explicit search or a knowledge synthesis request
            if any(term in q_lower for term in ["find", "search", "list threads", "show threads", "lookup"]):
                semantic_capability = CapabilityType.CONVERSATION_SEARCH_SERVICE
                semantic_request_intent = RequestIntent.CONVERSATION_QUERY
            else:
                semantic_capability = CapabilityType.KNOWLEDGE_SYNTHESIS
                semantic_request_intent = RequestIntent.CONVERSATION_QUERY
        elif intent_result.intent == IntentType.WORKSPACE_QUERY:
            if any(term in q_lower for term in ["how many", "count", "number of", "how many pdf", "how many document"]):
                semantic_capability = CapabilityType.SQL_METADATA
                semantic_request_intent = RequestIntent.WORKSPACE_META_QUERY
            else:
                semantic_capability = CapabilityType.KNOWLEDGE_SYNTHESIS
                semantic_request_intent = RequestIntent.KNOWLEDGE_QUERY
        elif intent_result.intent == IntentType.FOLLOW_UP:
            semantic_capability = CapabilityType.KNOWLEDGE_SYNTHESIS
            semantic_request_intent = RequestIntent.CONVERSATION_QUERY

        if semantic_capability:
            semantic_entities: Dict[str, Any] = {
                "source_hints": intent_result.source_hints,
                "scope": intent_result.scope.value,
                "rewritten_query": rewritten_query,
            }
            if intent_result.entities:
                semantic_entities["entities"] = [
                    {"text": e.text, "type": e.type, "source": e.source.value}
                    for e in intent_result.entities
                ]
            if intent_result.action_details:
                semantic_entities.update(intent_result.action_details.parameters or {})

            return RequestUnderstanding(
                intent=semantic_request_intent,
                request_type=semantic_request_type,
                confidence=1.0,
                rewritten_query=rewritten_query,
                entities=semantic_entities,
                temporal={
                    "raw_expression": intent_result.temporal.raw_expression,
                    "relative_days": intent_result.temporal.relative_days,
                    "start_date": intent_result.temporal.start_date,
                    "end_date": intent_result.temporal.end_date,
                    "granularity": intent_result.temporal.granularity,
                } if intent_result.temporal else {},
                conversation_refs={
                    "references": intent_result.references,
                    "rewritten_query": intent_result.rewritten_query,
                    "source_hints": intent_result.source_hints,
                },
                required_capability=semantic_capability,
                ambiguity=(intent_result.ambiguities[0].clarification_prompt if intent_result.ambiguities else None),
                response_mode=("CLARIFICATION_PROMPT" if intent_result.requires_clarification else ("ACTION_PROPOSAL" if intent_result.intent == IntentType.ACTION_REQUEST else "GROUNDED_ANSWER")),
                raw_query=clean_query
            )

        # 6. AI Action History Queries ("What did AI do for me today?", "What did you do for me today?")
        if any(phrase in q_lower for phrase in ["what did ai do", "what did you do for me", "what actions did ai", "ai actions today"]):
            return RequestUnderstanding(
                intent=RequestIntent.ACTION_HISTORY_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.ACTION_AUDIT_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # 6. Multi-Document Comparison Queries ("Compare the two reports", "Compare the two deployment documents")
        if "compare" in q_lower and any(w in q_lower for w in ["document", "documents", "report", "reports", "two", "both", "files"]):
            return RequestUnderstanding(
                intent=RequestIntent.MULTI_DOC_COMPARE,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.MULTI_DOC_COMPARE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # 7. Domain Queries (Tasks, Projects, Decisions, Graph, Metadata)
        # Metadata / Structured Count Queries
        if any(phrase in q_lower for phrase in ["how many pdf", "how many document", "how many project", "how many task", "what documents do we have", "what files do we have"]):
            return RequestUnderstanding(
                intent=RequestIntent.WORKSPACE_META_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.SQL_METADATA,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Task Queries (read-only)
        if any(phrase in q_lower for phrase in ["what tasks do i have", "what tasks do we have", "my tasks", "which tasks are pending", "which tasks are still pending", "tell me what's still pending", "what is pending", "anything overdue", "show pending tasks", "pending tasks", "who is working on", "who is responsible"]) and not any(verb in q_lower for verb in ["add", "put", "create", "make", "assign", "set", "remind", "tell", "every"]):
            return RequestUnderstanding(
                intent=RequestIntent.TASK_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.TASK_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Reminder Queries (read-only)
        if any(phrase in q_lower for phrase in ["what reminders do i have", "what reminders do we have", "my reminders", "show reminders", "show my reminders", "list reminders"]):
            return RequestUnderstanding(
                intent=RequestIntent.REMINDER_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.TASK_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Automation Queries (read-only)
        if any(phrase in q_lower for phrase in ["what automations do i have", "what automations do we have", "my automations", "show automations", "show my automations", "list automations"]):
            return RequestUnderstanding(
                intent=RequestIntent.AUTOMATION_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.TASK_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Direct Message Queries (read-only)
        if any(phrase in q_lower for phrase in ["what messages did i receive", "what messages do i have", "my messages", "show messages", "show my dms"]):
            return RequestUnderstanding(
                intent=RequestIntent.DM_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.TASK_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Decision Queries
        if any(phrase in q_lower for phrase in ["what did we decide", "decided about", "decision about", "what were the decisions"]):
            return RequestUnderstanding(
                intent=RequestIntent.DECISION_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.KNOWLEDGE_SYNTHESIS,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Knowledge Graph / Dependency Queries
        if any(phrase in q_lower for phrase in ["why is this task blocked", "why is that task blocked", "why is the deployment task blocked", "what does this project depend on", "why did this decision happen", "which task came from"]) or (("why is" in q_lower or "why are" in q_lower) and "blocked" in q_lower):
            return RequestUnderstanding(
                intent=RequestIntent.GRAPH_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.GRAPH_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Conversation History Search Queries
        if any(phrase in q_lower for phrase in ["find conversation", "search conversation", "find discussions", "search discussions"]):
            return RequestUnderstanding(
                intent=RequestIntent.CONVERSATION_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.CONVERSATION_SEARCH_SERVICE,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # Temporal Activity Queries
        if any(phrase in q_lower for phrase in ["what changed this week", "what changed recently", "what did i upload yesterday"]):
            return RequestUnderstanding(
                intent=RequestIntent.ACTIVITY_QUERY,
                request_type=RequestType.QUERY,
                confidence=1.0,
                required_capability=CapabilityType.SQL_METADATA,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        # 8. Action Intents (Task Creation, Reminders, Automations, Direct Messages)
        action_proposal = ActionClassifier.classify(clean_query)
        if action_proposal:
            req_intent = RequestIntent.UNKNOWN
            try:
                req_intent = RequestIntent(action_proposal.intent_type.value)
            except ValueError:
                req_intent = RequestIntent.CREATE_TASK

            if action_proposal.status == ActionStatus.NEEDS_CLARIFICATION:
                missing_params = ["title"] if action_proposal.intent_type.value == "CREATE_TASK" else ["time_str"]
                return RequestUnderstanding(
                    intent=req_intent,
                    request_type=RequestType.ACTION,
                    confidence=1.0,
                    required_capability=CapabilityType.ACTION_WORKFLOW,
                    missing_information=missing_params,
                    response_mode="CLARIFICATION_PROMPT",
                    raw_query=clean_query
                )
            else:
                return RequestUnderstanding(
                    intent=req_intent,
                    request_type=RequestType.ACTION,
                    confidence=1.0,
                    entities=action_proposal.parameters,
                    required_capability=CapabilityType.ACTION_WORKFLOW,
                    response_mode="ACTION_PROPOSAL",
                    raw_query=clean_query
                )

        # Fallback Decision: Workspace Knowledge vs General Question
        workspace_keywords = [
            "workspace", "document", "documents", "report", "reports", "file", "files",
            "pdf", "pdfs", "policy", "policies", "codebase", "mindmesh", "uploaded",
            "project", "projects", "task", "tasks", "decision", "decisions", "oauth",
            "deployment", "spec", "specification", "meeting", "architecture"
        ]

        if any(kw in q_lower for kw in workspace_keywords):
            return RequestUnderstanding(
                intent=RequestIntent.KNOWLEDGE_QUERY,
                request_type=RequestType.QUERY,
                confidence=0.8,
                required_capability=CapabilityType.KNOWLEDGE_SYNTHESIS,
                response_mode="GROUNDED_ANSWER",
                raw_query=clean_query
            )

        return RequestUnderstanding(
            intent=RequestIntent.GENERAL_KNOWLEDGE,
            request_type=RequestType.GENERAL_KNOWLEDGE,
            confidence=0.9,
            required_capability=CapabilityType.GENERAL_LLM,
            response_mode="DIRECT_ANSWER",
            raw_query=clean_query
        )
