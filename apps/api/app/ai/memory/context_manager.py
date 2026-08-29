import time
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory.context_models import (
    ConversationContext,
    ConversationTopic,
    ConversationFact,
    ResolvedReference
)
from app.ai.memory.reference_resolver import ReferenceResolver
from app.ai.memory.topic_tracker import TopicTracker
from app.ai.memory.fact_tracker import FactTracker
from app.ai.memory.context_budget import ContextBudgetManager
from app.ai.chat.session import ChatSessionManager

logger = logging.getLogger(__name__)

class ConversationContextManager:
    """
    MindMesh Conversation Memory & Context Manager.
    
    Responsibilities:
    - Multi-layer memory assembly (Current Message, Recent Window, Summary, Extracted Facts, Long-Term Hook)
    - Reference & pronoun resolution (e.g. 'it' -> 'Project Alpha')
    - Active topic tracking & topic transitions
    - Context relevance scoring & budget enforcement
    - Prompt serialization for downstream AI generation
    """

    @classmethod
    async def build_conversation_context(
        cls,
        db: Optional[AsyncSession],
        conversation_id: UUID,
        user_id: UUID,
        organization_id: UUID,
        query: str,
        intent_result: Any,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        ui_context: Optional[Dict[str, Any]] = None,
        existing_context: Optional[ConversationContext] = None
    ) -> ConversationContext:
        start_time = time.time()

        # 1. Load History if not provided
        history: List[Dict[str, Any]] = conversation_history or []
        if not history and db:
            db_msgs = await ChatSessionManager.list_messages(db, conversation_id, organization_id, limit=50)
            history = [{"id": str(m.id), "role": m.role, "content": m.content, "created_at": m.created_at} for m in db_msgs]

        # 2. Reference & Pronoun Resolution
        resolved_refs = ReferenceResolver.resolve(query, history, intent_result)

        # 3. Active Topic Tracking & Context Reset Check
        prev_topics = existing_context.active_topics if existing_context else []
        active_topics, is_reset = TopicTracker.track(query, intent_result, prev_topics, history)

        if is_reset:
            history = []  # Clear historical carryover for reset query
            resolved_refs = []

        # 4. Fact & Preference Extraction
        prev_facts = existing_context.facts if existing_context else []
        prev_prefs = existing_context.user_preferences if existing_context else {}
        facts, user_prefs = FactTracker.extract_facts_and_preferences(query, prev_facts, prev_prefs)

        # 5. Context Ranking & Token Budgeting
        budgeted_messages = ContextBudgetManager.rank_and_select(
            current_query=query,
            history=history,
            intent_result=intent_result,
            max_messages=10,
            max_tokens=2500
        )

        # 6. Format Model Prompt Text
        prompt_lines = []
        if active_topics:
            prompt_lines.append(f"ACTIVE TOPIC: {active_topics[0].topic_label}")

        if resolved_refs:
            ref_str = ", ".join([f"'{r.reference_text}' -> {r.resolved_entity}" for r in resolved_refs])
            prompt_lines.append(f"RESOLVED CONTEXTUAL REFERENCES: {ref_str}")

        if user_prefs:
            pref_str = ", ".join([f"{k}: {v}" for k, v in user_prefs.items()])
            prompt_lines.append(f"USER CONVERSATIONAL PREFERENCES: {pref_str}")

        if facts:
            active_facts = [f.content for f in facts if f.fact_status.value != "EXPIRED"]
            if active_facts:
                prompt_lines.append("EXTRACTED CONVERSATION FACTS:\n" + "\n".join([f"- {af}" for af in active_facts[-5:]]))

        if budgeted_messages:
            prompt_lines.append("RECENT CONVERSATION HISTORY:")
            for m in budgeted_messages:
                role = m.get("role", "user").capitalize()
                content = m.get("content") or m.get("text") or ""
                prompt_lines.append(f"{role}: {content}")

        context_prompt_text = "\n\n".join(prompt_lines) if prompt_lines else "No prior conversation context."

        src_ids = [str(m.get("id")) for m in budgeted_messages if m.get("id")]

        return ConversationContext(
            conversation_id=conversation_id,
            current_message_text=query,
            recent_messages=budgeted_messages,
            summary=existing_context.summary if existing_context else None,
            active_topics=active_topics,
            entities=[e.to_dict() if hasattr(e, "to_dict") else str(e) for e in getattr(intent_result, "entities", [])],
            resolved_references=resolved_refs,
            facts=facts,
            user_preferences=user_prefs,
            context_timestamp=time.time(),
            source_message_ids=src_ids,
            version=(existing_context.version + 1) if existing_context else 1,
            context_prompt_text=context_prompt_text
        )
