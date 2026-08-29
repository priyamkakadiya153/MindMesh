import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ContextResolver:
    """
    Resolves entity references, pronouns, and pending action states across conversation history.
    """

    PRONOUN_PATTERNS = [
        re.compile(r"\b(which one|which project|which task|which report|the delayed one|the active one)\b", re.IGNORECASE),
        re.compile(r"\b(when was that|what was that|why did that happen|what happened after that|how about that)\b", re.IGNORECASE),
        re.compile(r"\b(which document contains it|show me it|where is it|what about it)\b", re.IGNORECASE),
        re.compile(r"\b(it|that|this|the first one|the second one|that project|that task|that decision|the report)\b", re.IGNORECASE),
    ]

    @classmethod
    def resolve_references(
        cls,
        query: str,
        history: Optional[List[Dict[str, Any]]] = None,
        pending_action: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyzes conversation history and extracts resolved referents for pronouns/references.
        """
        refs = {
            "has_reference": False,
            "referent_type": None,
            "resolved_entity": None,
            "resolved_query": query,
            "pending_fill": None,
            "followup_goal": None
        }

        q_lower = query.lower().strip()

        # Check if query is answering a clarification prompt for a pending action
        if pending_action:
            intent = pending_action.get("intent")
            missing = pending_action.get("missing", [])
            
            # Check for topic abandonment / new intent starter in user query
            is_new_topic = any(phrase in q_lower for phrase in [
                "actually", "remind me", "set a reminder", "create a task", "add a task",
                "message", "tell ", "let ", "what is", "how many", "nevermind", "cancel"
            ])
            
            if not is_new_topic:
                if intent == "CREATE_TASK" and ("title" in missing or not pending_action.get("title")):
                    refs["pending_fill"] = {
                        "action_intent": "CREATE_TASK",
                        "fill_field": "title",
                        "value": query.strip().capitalize()
                    }
                    return refs
                elif intent == "CREATE_REMINDER" and ("time_str" in missing or "time" in missing or not pending_action.get("time_str")):
                    rem_text = pending_action.get("reminder_text") or "Review files"
                    refs["pending_fill"] = {
                        "action_intent": "CREATE_REMINDER",
                        "fill_field": "time_str",
                        "reminder_text": rem_text,
                        "value": query.strip()
                    }
                    return refs

        if not history:
            return refs

        # Inspect last assistant turn and last user turn so pronouns can resolve
        # against the user's previous goal, not just the model's last reply.
        last_asst_msg = None
        last_user_msg = None
        for msg in reversed(history):
            role = msg.get("role") or msg.get("sender")
            content = (msg.get("content") or "").strip()
            if role == "assistant" and last_asst_msg is None:
                last_asst_msg = content
            elif role == "user":
                if content.lower() == q_lower:
                    continue  # skip current message being processed
                if last_user_msg is None:
                    last_user_msg = content
            if last_asst_msg and last_user_msg:
                break

        # Check pronoun / reference matches
        if any(pat.search(q_lower) for pat in cls.PRONOUN_PATTERNS) or "put that" in q_lower or "add that" in q_lower or "put it" in q_lower or "add it" in q_lower:
            refs["has_reference"] = True

            if last_user_msg:
                followup_goal = cls._extract_followup_goal(last_user_msg)
                if followup_goal:
                    refs["followup_goal"] = followup_goal
                    refs["resolved_query"] = followup_goal.get("resolved_query", query)

        if not last_asst_msg:
            return refs
            
            # Extract mentioned entities from last assistant message
            # Look for project names, decision topics, task titles, document titles
            asst_lower = last_asst_msg.lower()
            
            # Projects in last message
            proj_matches = re.findall(r"\b(Project\s+[A-Za-z0-9_\-]+|Primary Workspace Project|[A-Z][a-zA-Z0-9\s]+Project)\b", last_asst_msg)
            if "which one" in q_lower or "the delayed one" in q_lower or "which project" in q_lower:
                refs["referent_type"] = "PROJECT"
                refs["resolved_entity"] = proj_matches if proj_matches else ["active_projects"]
                refs["resolved_query"] = f"Which project among {proj_matches or 'the active projects'} is delayed or needs attention?"

            elif "when was that" in q_lower or "decision" in asst_lower:
                refs["referent_type"] = "DECISION"
                # Extract decision topic if present
                refs["resolved_entity"] = "OAuth decision" if "oauth" in asst_lower else "previous_decision"
                refs["resolved_query"] = f"When was the decision mentioned in '{last_asst_msg[:80]}' made?"

            elif "which document contains it" in q_lower or "document" in asst_lower:
                refs["referent_type"] = "DOCUMENT"
                refs["resolved_entity"] = "deployment_spec" if "deployment" in asst_lower else "relevant_document"
                refs["resolved_query"] = f"Which document contains details about the decision or topic in '{last_asst_msg[:80]}'?"

            elif "that task" in q_lower or "why is that task blocked" in q_lower or "task" in asst_lower:
                refs["referent_type"] = "TASK"
                refs["resolved_entity"] = "deployment task" if "deployment" in asst_lower else "blocked_task"
                refs["resolved_query"] = f"Why is the task referenced in '{last_asst_msg[:80]}' blocked?"

        return refs

    @staticmethod
    def _extract_followup_goal(user_message: str) -> Optional[Dict[str, Any]]:
        """Extracts a compact goal model from the previous user turn."""
        q = user_message.strip()
        q_lower = q.lower()

        task_match = re.search(
            r"(?:i need to|i have to|remember to|i want to|can you remind me to|review|check|follow up on|put|add)\s+(.*)",
            q,
            re.IGNORECASE,
        )
        if not task_match:
            return None

        tail = task_match.group(1).strip()
        tail = re.sub(r"\b(tomorrow|today|tonight|later|this week|next week|next monday|next tuesday|next wednesday|next thursday|next friday|next saturday|next sunday)\b.*$", "", tail, flags=re.IGNORECASE).strip()
        tail = re.sub(r"\b(by|on|at)\s+.*$", "", tail, flags=re.IGNORECASE).strip()
        tail = tail.strip(".?!, ")

        if not tail:
            return None

        title = tail[0].upper() + tail[1:] if len(tail) > 1 else tail.upper()
        due_date_str = None
        due_match = re.search(r"\b(tomorrow|today|tonight|later|this week|next week|next monday|next tuesday|next wednesday|next thursday|next friday|next saturday|next sunday)\b", q_lower, re.IGNORECASE)
        if due_match:
            due_date_str = due_match.group(1)

        return {
            "title": title,
            "due_date_str": due_date_str,
            "resolved_query": f"Create a task for {title}" + (f" due {due_date_str}" if due_date_str else "")
        }
