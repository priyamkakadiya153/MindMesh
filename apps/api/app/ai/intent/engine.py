import re
import logging
import time
from typing import Dict, Any, List, Optional
from uuid import UUID

from app.ai.intent.models import (
    IntentType,
    QueryType,
    ScopeType,
    ConfidenceLevel,
    QueryComplexity,
    IntentResult,
    EntityMention,
    EntitySource,
    ActionDetail,
    RoutingHints
)
from app.ai.intent.entity_extractor import EntityExtractor
from app.ai.intent.temporal_parser import TemporalParser
from app.ai.intent.followup_detector import FollowUpDetector
from app.ai.intent.query_rewriter import QueryRewriter
from app.ai.intent.ambiguity_detector import AmbiguityDetector

logger = logging.getLogger(__name__)

class IntentEngine:
    """
    MindMesh Intent & Query Understanding Engine.
    
    Transforms raw user messages into structured, normalized IntentResult representations
    to guide downstream retrieval, reasoning, memory, tool, and response orchestration layers.
    """

    GREETING_WORDS = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening"}
    THANKS_WORDS = {"thanks", "thank you", "thanks!", "thank you!", "okay", "ok", "great", "got it"}

    GENERAL_KNOWLEDGE_PATTERNS = [
        re.compile(r"^\s*(what is|calculate|compute|how much is|can you add|add)?\s*(\d+\s*[\+\-\*\/\,\s]+\s*\d+|\d+\s+(plus|minus|times|divided by)\s+\d+)\s*\??$", re.IGNORECASE),
        re.compile(r"^\s*[\d\s\+\-\*\/\(\)\.]+\s*\??$", re.IGNORECASE),
        re.compile(r"^\s*(what is|explain|how does|definition of|define|what does|why is|why does|why are)\s+(an\s+|a\s+|the\s+)?(polymorphism|recursion|http|tcp|rest|api|graphql|docker|kubernetes|react hooks|python|addition|subtraction|multiplication|division|sky blue|ocean blue|earth|sun|moon|light)\b", re.IGNORECASE),
        re.compile(r"\b(why is the sky blue|why is the ocean blue|what is 2 \+ 2|what is an api)\b", re.IGNORECASE)
    ]

    @classmethod
    def _normalize_query(cls, raw_query: str) -> str:
        clean = raw_query.strip()
        clean = re.sub(r"\s+", " ", clean)
        return clean

    @classmethod
    def _detect_language(cls, query: str) -> str:
        # Gujarati script unicode range: \u0A80-\u0AFF
        if re.search(r"[\u0A80-\u0AFF]", query):
            return "Gujarati"
        elif re.search(r"[\u0900-\u097F]", query):
            return "Hindi"
        elif any(w in query.lower().split() for w in ["hola", "gracias", "por", "favor"]):
            return "Spanish"
        return "English"

    @classmethod
    def understand_query(
        cls,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        ui_context: Optional[Dict[str, Any]] = None,
        user_metadata: Optional[Dict[str, Any]] = None
    ) -> IntentResult:
        start_time = time.time()
        norm_query = cls._normalize_query(query)
        q_lower = norm_query.lower()
        words = q_lower.split()

        lang = cls._detect_language(query)

        # 1. Entity Extraction & Temporal Parsing
        entities, references = EntityExtractor.extract(norm_query, conversation_history)
        temporal = TemporalParser.parse(norm_query)

        # 2. Check Ambiguities
        requires_clarification, ambiguities = AmbiguityDetector.detect(norm_query, entities, ui_context)

        # 3. Check Follow-up Status
        is_followup = FollowUpDetector.is_followup(norm_query, conversation_history)
        rewritten_q, ref_entity = QueryRewriter.rewrite(norm_query, conversation_history)
        if ref_entity and not any(e.text == ref_entity for e in entities):
            entities.append(EntityMention(text=ref_entity, type="Project", source=EntitySource.CONTEXTUAL))

        # 4. Stage 1: Fast-Path Rule Classifier
        contains_knowledge_keywords = any(w in q_lower for w in [
            "project", "document", "pdf", "task", "decision", "who", "where", "active", "status", "deadline",
            "architecture", "architectural", "report", "create", "open", "workspace", "file", "secret",
            "code", "discussion", "extract", "summar", "what did", "which"
        ])

        # Greeting only vs Greeting + Question
        is_pure_greeting = q_lower.strip("!?. ") in cls.GREETING_WORDS and not contains_knowledge_keywords
        is_greeting_prefix = any(q_lower.startswith(w) for w in cls.GREETING_WORDS)

        if is_pure_greeting:
            return cls._build_result(
                intent=IntentType.GREETING,
                query=query,
                norm_query=norm_query,
                lang=lang,
                req_retrieval=False,
                scope=ScopeType.GENERAL,
                entities=entities,
                references=references,
                temporal=temporal,
                complexity=QueryComplexity.SIMPLE,
                start_time=start_time
            )

        if q_lower.strip("!?. ") in cls.THANKS_WORDS:
            return cls._build_result(
                intent=IntentType.THANKS,
                query=query,
                norm_query=norm_query,
                lang=lang,
                req_retrieval=False,
                scope=ScopeType.GENERAL,
                entities=entities,
                references=references,
                temporal=temporal,
                complexity=QueryComplexity.SIMPLE,
                start_time=start_time
            )

        # Ambiguous addition / concept queries ("what addition?", "what is addition?")
        clean_ambig = q_lower.strip("!?. ")
        if clean_ambig in ["what addition", "addition", "add something", "can you add something", "can you add"]:
            return cls._build_result(
                intent=IntentType.AMBIGUOUS,
                query=query,
                norm_query=norm_query,
                lang=lang,
                req_retrieval=False,
                scope=ScopeType.GENERAL,
                entities=entities,
                references=references,
                temporal=temporal,
                complexity=QueryComplexity.SIMPLE,
                start_time=start_time
            )

        # General Knowledge Fast-Path
        for pat in cls.GENERAL_KNOWLEDGE_PATTERNS:
            if pat.search(q_lower) and not contains_knowledge_keywords:
                return cls._build_result(
                    intent=IntentType.GENERAL_KNOWLEDGE,
                    query=query,
                    norm_query=norm_query,
                    lang=lang,
                    req_retrieval=False,
                    scope=ScopeType.GENERAL,
                    entities=entities,
                    references=references,
                    temporal=temporal,
                    complexity=QueryComplexity.SIMPLE,
                    start_time=start_time
                )

        # 5. Stage 2: Intent Classification & Characteristics
        sub_intents = []
        if is_greeting_prefix and contains_knowledge_keywords:
            sub_intents.append(IntentType.GREETING)

        intent = IntentType.UNKNOWN
        scope = ScopeType.WORKSPACE
        query_type = QueryType.QUESTION
        req_retrieval = True
        source_hints = []
        action_detail = None
        req_tool = False

        # Action Intent ("Create a task...", "Open Project Alpha")
        if q_lower.startswith("create ") or "create a task" in q_lower or "create task" in q_lower:
            intent = IntentType.ACTION_REQUEST
            query_type = QueryType.COMMAND
            req_retrieval = False
            req_tool = True
            
            task_title = "New Task"
            if "called " in q_lower:
                task_title = norm_query.split("called ", 1)[1].strip("!?. ")
            elif "task " in q_lower:
                task_title = norm_query.split("task ", 1)[1].strip("!?. ")

            action_detail = ActionDetail(
                verb="CREATE",
                target="TASK",
                parameters={"title": task_title, "priority": "high" if "high" in q_lower else "normal"}
            )
        elif q_lower.startswith("open ") or q_lower.startswith("take me to "):
            intent = IntentType.NAVIGATION_REQUEST
            query_type = QueryType.NAVIGATION
            req_retrieval = False
            req_tool = True
            action_detail = ActionDetail(
                verb="OPEN",
                target="RESOURCE",
                parameters={"target_name": norm_query.split(" ", 1)[1] if " " in norm_query else norm_query}
            )
        elif "should i create" in q_lower:
            intent = IntentType.EXPLANATION_REQUEST
            query_type = QueryType.QUESTION
            req_retrieval = True
            source_hints = ["task", "project"]
        elif is_followup:
            intent = IntentType.FOLLOW_UP
            req_retrieval = True
            source_hints = ["conversation", "project"]
        elif (q_lower.startswith("find ") or q_lower.startswith("search ") or "find conversation" in q_lower or "search conversation" in q_lower or "find message" in q_lower or "search message" in q_lower or "find threads" in q_lower):
            intent = IntentType.SEARCH_QUERY
            query_type = QueryType.SEARCH
            source_hints = ["conversation", "document", "task"]
        elif "extract " in q_lower or "extraction" in q_lower or ("extract" in q_lower and ("task" in q_lower or "decision" in q_lower or "deadline" in q_lower or "responsibilit" in q_lower)):
            intent = IntentType.EXTRACTION_REQUEST
            query_type = QueryType.REQUEST
            source_hints = ["conversation", "document", "task", "decision"]
        elif "summarize" in q_lower or "summary" in q_lower or "recap" in q_lower:
            intent = IntentType.SUMMARY_REQUEST
            query_type = QueryType.SUMMARY
            source_hints = ["document", "conversation", "meeting", "task", "decision"]
        elif "decide" in q_lower or "decision" in q_lower:
            intent = IntentType.DECISION_QUERY
            scope = ScopeType.DECISION
            source_hints = ["decision", "conversation", "document"]
        elif "compare" in q_lower or "versus" in q_lower or "difference" in q_lower:
            intent = IntentType.COMPARISON_REQUEST
            query_type = QueryType.COMPARISON
            source_hints = ["document", "project"]
        elif "pdf" in q_lower or "document" in q_lower or "file" in q_lower or "report" in q_lower:
            intent = IntentType.DOCUMENT_QUERY
            scope = ScopeType.DOCUMENT
            source_hints = ["document"]
        elif "project" in q_lower or "roadmap" in q_lower or "milestone" in q_lower:
            intent = IntentType.PROJECT_QUERY
            scope = ScopeType.PROJECT
            source_hints = ["project", "document"]
        elif "task" in q_lower or "todo" in q_lower or "assignee" in q_lower:
            intent = IntentType.TASK_QUERY
            scope = ScopeType.TASK
            source_hints = ["task", "conversation"]
        elif "polymorphism" in q_lower or "recursion" in q_lower or "kubernetes" in q_lower:
            intent = IntentType.GENERAL_KNOWLEDGE
            scope = ScopeType.GENERAL
            req_retrieval = False
        else:
            intent = IntentType.WORKSPACE_QUERY
            source_hints = ["document", "project", "task", "decision", "conversation"]

        # Complexity determination
        complexity = QueryComplexity.SIMPLE
        if len(norm_query.split()) > 12 or len(sub_intents) > 0 or "compare" in q_lower:
            complexity = QueryComplexity.COMPLEX
        elif len(norm_query.split()) > 6:
            complexity = QueryComplexity.MODERATE

        return cls._build_result(
            intent=intent,
            sub_intents=sub_intents,
            query=query,
            norm_query=norm_query,
            rewritten_query=rewritten_q,
            lang=lang,
            query_type=query_type,
            scope=scope,
            req_retrieval=req_retrieval,
            source_hints=source_hints,
            entities=entities,
            references=references,
            temporal=temporal,
            req_conv_ctx=is_followup or (conversation_history is not None and len(conversation_history) > 0),
            req_tool=req_tool,
            action_detail=action_detail,
            req_clarification=requires_clarification,
            ambiguities=ambiguities,
            complexity=complexity,
            start_time=start_time
        )

    @classmethod
    def _build_result(
        cls,
        intent: IntentType,
        query: str,
        norm_query: str,
        lang: str,
        req_retrieval: bool,
        scope: ScopeType,
        entities: List[EntityMention],
        references: List[str],
        temporal: Optional[Any],
        complexity: QueryComplexity,
        start_time: float,
        sub_intents: Optional[List[IntentType]] = None,
        rewritten_query: Optional[str] = None,
        query_type: QueryType = QueryType.QUESTION,
        source_hints: Optional[List[str]] = None,
        req_conv_ctx: bool = False,
        req_tool: bool = False,
        action_detail: Optional[ActionDetail] = None,
        req_clarification: bool = False,
        ambiguities: Optional[List[Any]] = None,
    ) -> IntentResult:
        hints = RoutingHints(
            needs_general_model=(intent in {IntentType.GREETING, IntentType.GENERAL_KNOWLEDGE, IntentType.THANKS}),
            needs_workspace_retrieval=req_retrieval,
            needs_structured_data=("task" in (source_hints or []) or intent == IntentType.TASK_QUERY),
            needs_document_search=(intent == IntentType.DOCUMENT_QUERY or "document" in (source_hints or [])),
            needs_conversation_search=(intent in {IntentType.CONVERSATION_QUERY, IntentType.MEETING_QUERY, IntentType.FOLLOW_UP}),
            needs_tool=req_tool,
            needs_multi_step_reasoning=(complexity == QueryComplexity.COMPLEX),
            needs_clarification=req_clarification
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return IntentResult(
            intent=intent,
            sub_intents=sub_intents or [],
            confidence=ConfidenceLevel.HIGH,
            query=query,
            normalized_query=norm_query,
            rewritten_query=rewritten_query,
            query_type=query_type,
            scope=scope,
            entities=entities,
            references=references,
            temporal=temporal,
            requires_retrieval=req_retrieval,
            source_hints=source_hints or [],
            requires_conversation_context=req_conv_ctx,
            requires_tool=req_tool,
            action_details=action_detail,
            requires_clarification=req_clarification,
            ambiguities=ambiguities or [],
            language=lang,
            complexity=complexity,
            routing_hints=hints,
            metadata={"classification_latency_ms": latency_ms}
        )
