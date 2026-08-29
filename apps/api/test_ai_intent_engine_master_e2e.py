import pytest
from app.ai.intent.models import (
    IntentType,
    QueryType,
    ScopeType,
    ConfidenceLevel,
    QueryComplexity,
    IntentResult
)
from app.ai.intent.engine import IntentEngine
from app.ai.intent.entity_extractor import EntityExtractor
from app.ai.intent.temporal_parser import TemporalParser
from app.ai.intent.followup_detector import FollowUpDetector
from app.ai.intent.query_rewriter import QueryRewriter
from app.ai.intent.ambiguity_detector import AmbiguityDetector

def test_greeting_intent():
    res = IntentEngine.understand_query("hi")
    assert res.intent == IntentType.GREETING
    assert res.requires_retrieval is False
    assert res.scope == ScopeType.GENERAL
    assert res.routing_hints.needs_general_model is True
    assert res.routing_hints.needs_workspace_retrieval is False

def test_greeting_plus_question_intent():
    res = IntentEngine.understand_query("hi, what projects are active?")
    assert res.intent in {IntentType.PROJECT_QUERY, IntentType.WORKSPACE_QUERY}
    assert IntentType.GREETING in res.sub_intents
    assert res.requires_retrieval is True

def test_general_knowledge_intent():
    res1 = IntentEngine.understand_query("What is polymorphism?")
    assert res1.intent == IntentType.GENERAL_KNOWLEDGE
    assert res1.requires_retrieval is False

    res2 = IntentEngine.understand_query("Explain React hooks.")
    assert res2.intent == IntentType.GENERAL_KNOWLEDGE
    assert res2.requires_retrieval is False

def test_workspace_and_document_query():
    res = IntentEngine.understand_query("What does the architecture PDF say about authentication?")
    assert res.intent == IntentType.DOCUMENT_QUERY
    assert res.requires_retrieval is True
    assert res.routing_hints.needs_document_search is True

def test_task_and_decision_query():
    res_task = IntentEngine.understand_query("Which tasks are overdue?")
    assert res_task.intent == IntentType.TASK_QUERY
    assert res_task.requires_retrieval is True

    res_dec = IntentEngine.understand_query("Why did we decide to use FastAPI?")
    assert res_dec.intent == IntentType.DECISION_QUERY
    assert res_dec.requires_retrieval is True

def test_followup_and_query_rewriting():
    history = [
        {"role": "user", "content": "Tell me about active projects"},
        {"role": "assistant", "content": "Project Alpha and Project Beta are active."}
    ]

    res = IntentEngine.understand_query("What about the first one?", conversation_history=history)
    assert res.intent == IntentType.FOLLOW_UP
    assert res.requires_conversation_context is True
    assert res.rewritten_query is not None
    assert "Project Alpha" in res.rewritten_query

def test_temporal_parsing():
    res = IntentEngine.understand_query("What happened yesterday?")
    assert res.temporal is not None
    assert res.temporal.raw_expression.lower() == "yesterday"
    assert res.temporal.relative_days == -1
    assert res.temporal.granularity == "day"

def test_action_request_parsing():
    res = IntentEngine.understand_query("Create a task called Fix Login")
    assert res.intent == IntentType.ACTION_REQUEST
    assert res.query_type == QueryType.COMMAND
    assert res.requires_tool is True
    assert res.action_details is not None
    assert res.action_details.verb == "CREATE"
    assert res.action_details.target == "TASK"
    assert res.action_details.parameters.get("title") == "Fix Login"

def test_ambiguity_detection_and_clarification():
    res = IntentEngine.understand_query("Open the report")
    assert res.requires_clarification is True
    assert len(res.ambiguities) > 0
    assert res.ambiguities[0].clarification_prompt is not None

def test_language_detection():
    res_guj = IntentEngine.understand_query("નમસ્તે, મારો પ્રોજેક્ટ ક્યાં છે?")
    assert res_guj.language == "Gujarati"

    res_eng = IntentEngine.understand_query("What projects am I working on?")
    assert res_eng.language == "English"
