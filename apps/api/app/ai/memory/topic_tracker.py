import re
import time
from typing import List, Dict, Any, Optional, Tuple
from app.ai.memory.context_models import ConversationTopic, TopicState

class TopicTracker:
    """
    Manages active topics, topic transitions (Started, Continued, Shifted, Resumed), and explicit context resets.
    """

    RESET_PATTERNS = [
        re.compile(r"\b(forget the previous context|forget previous context|start a new topic|reset context|new question)\b", re.IGNORECASE)
    ]

    @classmethod
    def track(
        cls,
        query: str,
        intent_result: Any,
        existing_topics: List[ConversationTopic],
        history: List[Dict[str, Any]]
    ) -> Tuple[List[ConversationTopic], bool]:
        q_lower = query.lower().strip()

        # 1. Check Explicit Context Reset
        for pat in cls.RESET_PATTERNS:
            if pat.search(q_lower):
                return [], True

        # 2. Check Topic Resume ("Back to Project Alpha...")
        resume_match = re.search(r"\bback to (project\s+[a-zA-Z0-9_-]+|[a-zA-Z0-9_-]+)\b", q_lower)
        if resume_match:
            target_topic = resume_match.group(1).title()
            resumed_topic = ConversationTopic(
                topic_label=f"Project {target_topic}" if not target_topic.lower().startswith("project") else target_topic,
                state=TopicState.TOPIC_RESUMED,
                last_updated=time.time()
            )
            return [resumed_topic], False

        # 3. Check General Knowledge Topic Shift
        intent_val = getattr(intent_result, "intent", None)
        intent_str = intent_val.value if hasattr(intent_val, "value") else str(intent_val)

        if intent_str == "GENERAL_KNOWLEDGE":
            # Topic shifted away from previous workspace topics
            shifted_topic = ConversationTopic(
                topic_label="General Knowledge",
                scope="GENERAL",
                state=TopicState.TOPIC_SHIFTED,
                last_updated=time.time()
            )
            return [shifted_topic], False

        # 4. Workspace / Project Topic Continuation
        extracted_entities = getattr(intent_result, "entities", [])
        current_entity_names = [e.text for e in extracted_entities]

        if current_entity_names:
            main_topic = ConversationTopic(
                topic_label=current_entity_names[0],
                entities=current_entity_names,
                state=TopicState.TOPIC_CONTINUED if existing_topics else TopicState.TOPIC_STARTED,
                last_updated=time.time()
            )
            return [main_topic], False

        # Default: retain existing topics if active
        if existing_topics:
            existing_topics[0].state = TopicState.TOPIC_CONTINUED
            existing_topics[0].last_updated = time.time()
            return existing_topics, False

        default_topic = ConversationTopic(
            topic_label="Workspace Inquiry",
            state=TopicState.TOPIC_STARTED,
            last_updated=time.time()
        )
        return [default_topic], False
