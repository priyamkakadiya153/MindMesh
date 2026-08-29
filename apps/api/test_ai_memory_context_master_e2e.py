import uuid
import pytest
from app.ai.intent.engine import IntentEngine
from app.ai.memory.context_models import ConversationContext, FactStatus, TopicState
from app.ai.memory.reference_resolver import ReferenceResolver
from app.ai.memory.topic_tracker import TopicTracker
from app.ai.memory.fact_tracker import FactTracker
from app.ai.memory.context_budget import ContextBudgetManager
from app.ai.memory.context_manager import ConversationContextManager

def test_pronoun_reference_resolution():
    history = [
        {"role": "user", "content": "What projects are active?"},
        {"role": "assistant", "content": "Project Alpha is active."}
    ]
    refs = ReferenceResolver.resolve("Why is it delayed?", history)
    assert len(refs) > 0
    assert refs[0].resolved_entity == "Project Alpha"

def test_ordinal_reference_resolution():
    history = [
        {"role": "user", "content": "List top projects"},
        {"role": "assistant", "content": "Project Alpha, Project Beta, and Project Gamma."}
    ]
    refs = ReferenceResolver.resolve("What about the first one?", history)
    assert len(refs) > 0
    assert refs[0].resolved_entity == "Project Alpha"

    refs_second = ReferenceResolver.resolve("What about the second one?", history)
    assert len(refs_second) > 0
    assert refs_second[0].resolved_entity == "Project Beta"

def test_user_reference_correction():
    history = [
        {"role": "assistant", "content": "Analyzing Project Alpha..."}
    ]
    refs = ReferenceResolver.resolve("No, I meant Project Beta", history)
    assert len(refs) > 0
    assert refs[0].resolved_entity == "Project Beta"

def test_topic_shift_and_resume():
    intent_gk = IntentEngine.understand_query("What is recursion?")
    topics, is_reset = TopicTracker.track("What is recursion?", intent_gk, [], [])
    assert len(topics) > 0
    assert topics[0].state == TopicState.TOPIC_SHIFTED
    assert topics[0].topic_label == "General Knowledge"

    intent_resume = IntentEngine.understand_query("Back to Project Alpha — what was the deadline?")
    resumed_topics, _ = TopicTracker.track("Back to Project Alpha — what was the deadline?", intent_resume, topics, [])
    assert len(resumed_topics) > 0
    assert resumed_topics[0].state == TopicState.TOPIC_RESUMED
    assert "Alpha" in resumed_topics[0].topic_label

def test_context_reset():
    intent_reset = IntentEngine.understand_query("Forget the previous context")
    topics, is_reset = TopicTracker.track("Forget the previous context", intent_reset, [], [])
    assert is_reset is True
    assert len(topics) == 0

def test_fact_tracking_and_precedence():
    facts, prefs = FactTracker.extract_facts_and_preferences("My deadline is Friday", [], {})
    assert len(facts) == 1
    assert facts[0].fact_status == FactStatus.USER_STATED
    assert "Friday" in facts[0].content

    facts_updated, _ = FactTracker.extract_facts_and_preferences("Actually deadline changed to Monday", facts, {})
    assert len(facts_updated) == 2
    # First deadline fact should be marked EXPIRED
    assert facts_updated[0].fact_status == FactStatus.EXPIRED
    assert facts_updated[1].fact_status == FactStatus.USER_STATED
    assert "Monday" in facts_updated[1].content

def test_preference_tracking():
    facts, prefs = FactTracker.extract_facts_and_preferences("Keep answers short", [], {})
    assert prefs.get("verbosity") == "concise"

    facts2, prefs2 = FactTracker.extract_facts_and_preferences("Actually explain in detail", facts, prefs)
    assert prefs2.get("verbosity") == "detailed"

def test_context_budget_ranking():
    history = [
        {"id": "1", "role": "user", "content": "How does recursion work?"},
        {"id": "2", "role": "assistant", "content": "Recursion is when a function calls itself."},
        {"id": "3", "role": "user", "content": "Project Alpha deadline is September 20."}
    ]
    intent_res = IntentEngine.understand_query("What was that deadline?")
    selected = ContextBudgetManager.rank_and_select("What was that deadline?", history, intent_res, max_messages=2)
    assert len(selected) <= 2
    contents = [m["content"] for m in selected]
    assert any("September 20" in c for c in contents)

@pytest.mark.asyncio
async def test_build_conversation_context_integration():
    conv_id = uuid.uuid4()
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()

    history = [
        {"role": "user", "content": "Tell me about active projects"},
        {"role": "assistant", "content": "Project Alpha is active."}
    ]
    intent_res = IntentEngine.understand_query("Why is it delayed?", conversation_history=history)

    ctx = await ConversationContextManager.build_conversation_context(
        db=None,
        conversation_id=conv_id,
        user_id=user_id,
        organization_id=org_id,
        query="Why is it delayed?",
        intent_result=intent_res,
        conversation_history=history
    )

    assert ctx.conversation_id == conv_id
    assert len(ctx.resolved_references) > 0
    assert ctx.resolved_references[0].resolved_entity == "Project Alpha"
    assert "ACTIVE TOPIC" in ctx.context_prompt_text
    assert "RESOLVED CONTEXTUAL REFERENCES" in ctx.context_prompt_text
