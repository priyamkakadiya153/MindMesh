import logging
import re
from uuid import uuid4, UUID
from typing import Optional, Dict, Any, Tuple
from .types import ActionIntentType, ActionStatus, ActionProposal

logger = logging.getLogger(__name__)

READ_ONLY_STARTERS = [
    "what", "who", "where", "when", "why", "how many", "how much",
    "list", "show", "count", "find", "search", "tell me about", "are there"
]

ACTION_VERB_MAP = {
    "create a task": ActionIntentType.CREATE_TASK,
    "create task": ActionIntentType.CREATE_TASK,
    "add a task": ActionIntentType.CREATE_TASK,
    "add task": ActionIntentType.CREATE_TASK,
    "make a task": ActionIntentType.CREATE_TASK,
    "make task": ActionIntentType.CREATE_TASK,
    "new task": ActionIntentType.CREATE_TASK,

    "change the": ActionIntentType.UPDATE_TASK,
    "update task": ActionIntentType.UPDATE_TASK,
    "modify task": ActionIntentType.UPDATE_TASK,
    "rename the": ActionIntentType.UPDATE_TASK,
    "move the": ActionIntentType.UPDATE_TASK,

    "assign task": ActionIntentType.ASSIGN_TASK,
    "assign the": ActionIntentType.ASSIGN_TASK,
    "assign": ActionIntentType.ASSIGN_TASK,

    "complete task": ActionIntentType.COMPLETE_TASK,
    "mark the": ActionIntentType.COMPLETE_TASK,
    "mark as complete": ActionIntentType.COMPLETE_TASK,
    "finish task": ActionIntentType.COMPLETE_TASK,
    "close task": ActionIntentType.COMPLETE_TASK,

    "create reminder": ActionIntentType.CREATE_REMINDER,
    "remind me": ActionIntentType.CREATE_REMINDER,
    "cancel my reminder": ActionIntentType.CREATE_REMINDER,
    "cancel reminder": ActionIntentType.CREATE_REMINDER,
    "delete reminder": ActionIntentType.CREATE_REMINDER,

    "create decision": ActionIntentType.CREATE_DECISION,
    "record decision": ActionIntentType.CREATE_DECISION,

    "send message": ActionIntentType.SEND_DIRECT_MESSAGE,
    "send a message": ActionIntentType.SEND_DIRECT_MESSAGE,
    "send dm": ActionIntentType.SEND_DIRECT_MESSAGE,
    "message": ActionIntentType.SEND_DIRECT_MESSAGE,
    "tell": ActionIntentType.SEND_DIRECT_MESSAGE,
    "let": ActionIntentType.SEND_DIRECT_MESSAGE,

    "create automation": ActionIntentType.CREATE_AUTOMATION,
}

class ActionClassifier:
    """Classifies user queries into Action Proposals or Read-Only Queries."""

    @classmethod
    def classify(
        cls,
        query: str,
        workspace_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        resolved_context: Optional[Dict[str, Any]] = None
    ) -> Optional[ActionProposal]:
        q_lower = query.lower().strip()

        # Check for Level 3 Destructive Actions ("delete project", "delete document", "remove member")
        if any(w in q_lower for w in ["delete", "remove", "drop", "destroy"]) and any(w in q_lower for w in ["project", "document", "file", "workspace", "organization", "database", "member", "user"]) and "reminder" not in q_lower and "automation" not in q_lower:
            return ActionProposal(
                proposal_id=f"prop-{str(uuid4())[:8]}",
                intent_type=ActionIntentType.DELETE_DOCUMENT,
                title="Blocked Destructive Action",
                description="Destructive actions (such as project or document deletion) are disabled via AI Chat for safety.",
                parameters={"is_blocked": True},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=False,
                status=ActionStatus.FAILED
            )

        # Check for Action History Read-Only query ("what did ai do for me today?", "what actions did ai take?")
        if any(term in q_lower for term in ["what did ai do", "what actions did ai", "ai actions today", "what actions were taken", "show ai actions"]):
            return ActionProposal(
                proposal_id=f"prop-{str(uuid4())[:8]}",
                intent_type=ActionIntentType.CREATE_TASK,
                title="View Action History",
                parameters={"is_history_query": True},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=False,
                status=ActionStatus.CONFIRMED
            )

        # Check for Reminder Read-Only query ("what reminders do i have?", "show my reminders")
        if any(term in q_lower for term in ["what reminders", "show my reminders", "show reminders", "list reminders"]):
            return None

        # Check for Automations Read-Only query ("what automations do i have?", "show my automations")
        if any(term in q_lower for term in ["what automations", "show my automations", "show automations", "list automations"]):
            return None

        # Check for Task Read-Only query ("what tasks do i have?", "show my tasks")
        if any(term in q_lower for term in ["what tasks do i have", "what tasks", "show my tasks", "show tasks", "list tasks", "list my tasks", "what are my tasks"]) and not any(verb in q_lower for verb in ["add", "put", "create", "make", "assign", "set"]):
            return None

        proposal_id = f"prop-{str(uuid4())[:8]}"

        # Check for Update Automation Intent ("Change my weekly task review to Tuesday at 10 AM")
        if any(w in q_lower for w in ["change", "update", "modify", "move"]) and any(w in q_lower for w in ["weekly", "daily", "monthly", "automation", "task review", "review"]):
            if any(day in q_lower for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "am", "pm", "at "]):
                target_ref = re.sub(r'^(please\s+)?(change|update|modify|move)\s+(the\s+|my\s+)?', '', q_lower, flags=re.IGNORECASE)
                target_ref = re.split(r'\s+to\s+', target_ref, flags=re.IGNORECASE)[0].strip()
                return ActionProposal(
                    proposal_id=proposal_id,
                    intent_type=ActionIntentType.UPDATE_AUTOMATION,
                    title=f"Update Automation: {target_ref.title() or 'Automation'}",
                    description=f"Action proposal to update automation '{target_ref}'.",
                    parameters={"target_ref": target_ref, "management_action": "UPDATE", "raw_query": query},
                    workspace_id=str(workspace_id) if workspace_id else None,
                    user_id=str(user_id) if user_id else None,
                    confirmation_required=True,
                    status=ActionStatus.READY_FOR_CONFIRMATION
                )

        # Check for Management Intents (Pause, Resume, Cancel Automation)
        if "pause" in q_lower and any(w in q_lower for w in ["automation", "reminder", "task", "message", "one", "it", "review"]):
            target_ref = re.sub(r'^(please\s+)?pause\s+(the\s+|my\s+)?', '', q_lower, flags=re.IGNORECASE).strip()
            return ActionProposal(
                proposal_id=proposal_id,
                intent_type=ActionIntentType.PAUSE_AUTOMATION,
                title=f"Pause Automation: {target_ref.title() or 'Automation'}",
                description=f"Action proposal to pause automation '{target_ref}'.",
                parameters={"target_ref": target_ref, "management_action": "PAUSE"},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=True,
                status=ActionStatus.READY_FOR_CONFIRMATION
            )

        if "resume" in q_lower and any(w in q_lower for w in ["automation", "reminder", "task", "message", "one", "it", "review"]):
            target_ref = re.sub(r'^(please\s+)?resume\s+(the\s+|my\s+)?', '', q_lower, flags=re.IGNORECASE).strip()
            return ActionProposal(
                proposal_id=proposal_id,
                intent_type=ActionIntentType.RESUME_AUTOMATION,
                title=f"Resume Automation: {target_ref.title() or 'Automation'}",
                description=f"Action proposal to resume automation '{target_ref}'.",
                parameters={"target_ref": target_ref, "management_action": "RESUME"},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=True,
                status=ActionStatus.READY_FOR_CONFIRMATION
            )

        if any(term in q_lower for term in ["cancel automation", "cancel my automation", "delete automation", "delete my automation", "cancel the automation", "delete the automation", "stop automation", "stop my automation"]):
            target_ref = re.sub(r'^(please\s+)?(cancel|delete|stop)\s+(the\s+|my\s+)?', '', q_lower, flags=re.IGNORECASE).strip()
            return ActionProposal(
                proposal_id=proposal_id,
                intent_type=ActionIntentType.CANCEL_AUTOMATION,
                title=f"Cancel Automation: {target_ref.title() or 'Automation'}",
                description=f"Action proposal to cancel automation '{target_ref}'. Future executions will stop.",
                parameters={"target_ref": target_ref, "management_action": "CANCEL"},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=True,
                status=ActionStatus.READY_FOR_CONFIRMATION
            )

        # Check for Recurring / Automation Intent ("Remind me every Monday to review pending tasks", "Set up a weekly reminder for pending tasks")
        is_recurring = any(term in q_lower for term in ["every monday", "every tuesday", "every wednesday", "every thursday", "every friday", "every saturday", "every sunday", "every day", "every weekday", "every month", "weekly", "daily", "monthly", "recurring", "schedule a weekly", "schedule a daily"])
        if is_recurring or "automation" in q_lower:
            return cls._extract_create_automation_proposal(query, proposal_id, workspace_id, user_id)

        # 1. Read-Only Questions Protection
        if any(q_lower.startswith(prefix) for prefix in [
            "what tasks", "what reminders", "what automations", "what messages", "what project",
            "which task", "which project", "why is", "why are", "how many", "how much", "tell me what",
            "what did", "when did", "summarize my conversation", "show me our conversation"
        ]):
            return None

        is_question = any(q_lower.startswith(starter) for starter in READ_ONLY_STARTERS)
        is_explicit_action = any(kw in q_lower for kw in [
            "create a task", "add a task", "make a task", "new task", "to my tasks", "on my tasks", "to my task list", "on my task list", "to my todo", "on my todo",
            "change the", "move the", "rename the", "set the",
            "assign the", "assign", "mark the", "complete the", "mark as complete",
            "remind me", "create reminder", "cancel my reminder", "delete the reminder", "don't let me forget", "set a reminder",
            "message ", "send ", "tell ", "let "
        ])

        if is_question and not is_explicit_action:
            return None

        # 2. Semantic Intent Classification
        intent_type: Optional[ActionIntentType] = None
        if any(w in q_lower for w in ["cancel", "delete"]) and "reminder" in q_lower:
            intent_type = ActionIntentType.CREATE_REMINDER
        elif any(freq in q_lower for freq in ["every monday", "every tuesday", "every wednesday", "every thursday", "every friday", "every week", "weekly", "daily", "monthly"]) or "set up a weekly" in q_lower or "automation" in q_lower:
            intent_type = ActionIntentType.CREATE_AUTOMATION
        elif (
            re.search(r'\b(add|put|place|insert|append)\b.*\b(to|on|into|in)\b.*\b(task|tasks|todo|to-do|to do|list|action items?)\b', q_lower) or
            re.search(r'\b(create|make|set up|new)\b.*\b(task|tasks|todo|to-do|to do|action item)\b', q_lower) or
            re.search(r'\b(i need|i have to|remember to)\b.*\b(as a task|on my tasks|on my todo|to my tasks|to my task list)\b', q_lower) or
            re.search(r'\b(add|put|create|make)\b.*\b(something|item|this|it)?\b.*\b(i need to do|i have to do|to do|to my tasks|on my tasks|to my task list|on my task list|to my todo|on my todo)\b', q_lower) or
            re.search(r'\b(add|put|create|make)\b.*\b(a\s+)?(task|todo|to-do|to do)\b', q_lower) or
            re.search(r'\badd\s+it\s+to\s+my\s+tasks\b', q_lower) or
            re.search(r'\bcreat(e)?\b.*\btask\b', q_lower) or re.search(r'\badd\b.*\btask\b', q_lower) or re.search(r'\bmake\b.*\btask\b', q_lower) or re.search(r'\bnew\b.*\btask\b', q_lower)
        ):
            intent_type = ActionIntentType.CREATE_TASK
        elif re.search(r'\b(remind|reminder|don\'t let me forget|don\'t forget|don\'t want to forget|notify me|alert me)\b', q_lower):
            intent_type = ActionIntentType.CREATE_REMINDER
        elif re.search(r'\b(tell|message|send a message|send message|send a dm|send dm|let .* know|ping|inform)\b', q_lower) or (re.search(r'\bsend\b', q_lower) and re.search(r'\b(dm|message|to)\b', q_lower)) or q_lower.startswith("tell ") or q_lower.startswith("let "):
            intent_type = ActionIntentType.SEND_DIRECT_MESSAGE
        else:
            for kw, action_type in ACTION_VERB_MAP.items():
                if kw in q_lower:
                    intent_type = action_type
                    break

        if not intent_type:
            return None

        proposal_id = f"prop-{str(uuid4())[:8]}"

        # 3. Intent-Specific Parameter Extraction
        if intent_type == ActionIntentType.CREATE_TASK:
            return cls._extract_create_task_proposal(query, proposal_id, workspace_id, user_id, resolved_context=resolved_context)
        elif intent_type == ActionIntentType.UPDATE_TASK:
            return cls._extract_update_task_proposal(query, proposal_id, workspace_id, user_id)
        elif intent_type == ActionIntentType.ASSIGN_TASK:
            return cls._extract_assign_task_proposal(query, proposal_id, workspace_id, user_id)
        elif intent_type == ActionIntentType.COMPLETE_TASK:
            return cls._extract_complete_task_proposal(query, proposal_id, workspace_id, user_id)
        elif intent_type == ActionIntentType.CREATE_REMINDER:
            if "cancel" in q_lower or "delete" in q_lower:
                return cls._extract_cancel_reminder_proposal(query, proposal_id, workspace_id, user_id)
            return cls._extract_create_reminder_proposal(query, proposal_id, workspace_id, user_id)
        elif intent_type == ActionIntentType.SEND_DIRECT_MESSAGE:
            return cls._extract_send_message_proposal(query, proposal_id, workspace_id, user_id, resolved_context=resolved_context)
        else:
            return ActionProposal(
                proposal_id=proposal_id,
                intent_type=intent_type,
                title=intent_type.value.replace("_", " ").title(),
                parameters={"raw_query": query},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=True,
                status=ActionStatus.READY_FOR_CONFIRMATION
            )

    @classmethod
    def _extract_create_task_proposal(
        cls,
        query: str,
        proposal_id: str,
        workspace_id: Optional[UUID],
        user_id: Optional[UUID],
        resolved_context: Optional[Dict[str, Any]] = None
    ) -> ActionProposal:
        clean_query = query.rstrip('.!? ').strip()

        # Remove full structural command wrappers first
        title = clean_query
        title = re.sub(r'^(can you|could you|please|i need to|i have to|don\'t let me forget to|remember to)\s+', '', title, flags=re.IGNORECASE).strip()
        title = re.sub(r'^(add|put|place|create|make|set up|new)\s+', '', title, flags=re.IGNORECASE).strip()
        title = re.sub(r'^(a\s+)?(task|todo|to-do|to do)\s+(to|for|called|named)?\s*', '', title, flags=re.IGNORECASE).strip()

        # Remove target list suffixes
        title = re.sub(r'\s+(to|on|into|as)\s+(a\s+)?(my\s+)?(task\s+list|tasks|todo\s+list|todo|to-do|to do|list|action items?)$', '', title, flags=re.IGNORECASE).strip()
        title = re.sub(r'\s+as\s+a\s+task$', '', title, flags=re.IGNORECASE).strip()

        # Extract due date phrase first
        due_match = re.search(r'\b(by\s+|on\s+)?(tomorrow|today|tonight|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', query, re.IGNORECASE)
        due_date_str = due_match.group(0).strip().lower() if due_match else None

        if due_date_str:
            title = re.sub(r'\b(by\s+|on\s+)?(tomorrow|today|tonight|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', '', title, flags=re.IGNORECASE).strip()

        # Remove trailing/leading punctuation or filler words left after stripping
        title = re.sub(r'^(to|on|for|called|named)\s*', '', title, flags=re.IGNORECASE).strip()
        title = title.rstrip('.!? ').strip()

        generic_words = {"", "task", "a task", "something", "this", "that", "it", "that item", "the item", "that list", "that report", "that on my list", "this on my list", "it on my list", "item", "something to do", "to do", "my tasks", "my task list", "todo", "todo list", "to-do list", "me", "a task for me", "me a task", "i need to do", "something i need to do", "what i need to do"}

        # If title is generic or a relative pronoun, attempt to resolve from resolved_context / history
        resolved_goal = resolved_context.get("followup_goal") if resolved_context else None
        if resolved_goal and resolved_goal.get("title"):
            clean_title = resolved_goal["title"]
            resolved_due = due_date_str or resolved_goal.get("due_date_str")
            return ActionProposal(
                proposal_id=proposal_id,
                intent_type=ActionIntentType.CREATE_TASK,
                title=f"Create Task: {clean_title}",
                description=f"Action proposal to create task '{clean_title}'" + (f" due {resolved_due}" if resolved_due else "."),
                parameters={"title": clean_title, "due_date_str": resolved_due, "assignee_name": None},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=True,
                status=ActionStatus.READY_FOR_CONFIRMATION
            )

        if not title or title.lower() in generic_words or len(title) < 2:
            return ActionProposal(
                proposal_id=proposal_id,
                intent_type=ActionIntentType.CREATE_TASK,
                title="Create Task",
                parameters={},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=False,
                status=ActionStatus.NEEDS_CLARIFICATION,
                clarification_prompt="What would you like me to add to your task list?"
            )

        clean_title = title[0].upper() + title[1:] if len(title) > 0 else title

        assignee_match = re.search(r'\b(for|to|assign to)\s+([A-Z][a-z]+)\b', query)
        assignee_name = assignee_match.group(2) if assignee_match else None

        return ActionProposal(
            proposal_id=proposal_id,
            intent_type=ActionIntentType.CREATE_TASK,
            title=f"Create Task: {clean_title}",
            description=f"Action proposal to create task '{clean_title}'" + (f" due {due_date_str}" if due_date_str else "."),
            parameters={
                "title": clean_title,
                "description": f"Created via AI Chat: '{query}'",
                "assignee_name": assignee_name,
                "due_date_str": due_date_str
            },
            workspace_id=str(workspace_id) if workspace_id else None,
            user_id=str(user_id) if user_id else None,
            confirmation_required=True,
            status=ActionStatus.READY_FOR_CONFIRMATION
        )

    @classmethod
    def _extract_update_task_proposal(
        cls,
        query: str,
        proposal_id: str,
        workspace_id: Optional[UUID],
        user_id: Optional[UUID]
    ) -> ActionProposal:
        clean_query = query.rstrip('.').strip()
        kw_strip = re.sub(r'^(please\s+)?(change|update|modify|move|rename|set)\s+(the\s+)?', '', clean_query, flags=re.IGNORECASE)
        task_name = re.sub(r'\s+task\s+.*$', '', kw_strip, flags=re.IGNORECASE).strip()
        if task_name == kw_strip or not task_name:
            task_name = kw_strip.split()[0] if kw_strip else "Task"

        deadline_match = re.search(r'\bto\s+(friday|monday|tuesday|wednesday|thursday|saturday|sunday|tomorrow|next week|\d{1,2}\s+[A-Za-z]+)\b', clean_query, re.IGNORECASE)
        deadline_str = deadline_match.group(1) if deadline_match else None

        return ActionProposal(
            proposal_id=proposal_id,
            intent_type=ActionIntentType.UPDATE_TASK,
            title=f"Update Task: {task_name}",
            description=f"Action proposal to update task '{task_name}'.",
            parameters={
                "task_name": task_name,
                "new_deadline_str": deadline_str
            },
            workspace_id=str(workspace_id) if workspace_id else None,
            user_id=str(user_id) if user_id else None,
            confirmation_required=True,
            status=ActionStatus.READY_FOR_CONFIRMATION
        )

    @classmethod
    def _extract_assign_task_proposal(
        cls,
        query: str,
        proposal_id: str,
        workspace_id: Optional[UUID],
        user_id: Optional[UUID]
    ) -> ActionProposal:
        assignee_match = re.search(r'\bto\s+([A-Za-z]+)\b', query, re.IGNORECASE)
        assignee_name = assignee_match.group(1) if assignee_match else "Workspace Member"

        task_match = re.sub(r'^(please\s+)?assign\s+(the\s+)?', '', query, flags=re.IGNORECASE)
        task_name = task_match.split(" to ")[0].strip() if " to " in task_match else "Task"

        return ActionProposal(
            proposal_id=proposal_id,
            intent_type=ActionIntentType.ASSIGN_TASK,
            title=f"Assign Task: {task_name}",
            description=f"Action proposal to assign task '{task_name}' to {assignee_name}.",
            parameters={
                "task_name": task_name,
                "assignee_name": assignee_name
            },
            workspace_id=str(workspace_id) if workspace_id else None,
            user_id=str(user_id) if user_id else None,
            confirmation_required=True,
            status=ActionStatus.READY_FOR_CONFIRMATION
        )

    @classmethod
    def _extract_complete_task_proposal(
        cls,
        query: str,
        proposal_id: str,
        workspace_id: Optional[UUID],
        user_id: Optional[UUID]
    ) -> ActionProposal:
        clean_query = query.rstrip('.').strip()
        task_name = re.sub(r'^(please\s+)?(mark\s+the|complete\s+the|mark|complete)\s+', '', clean_query, flags=re.IGNORECASE)
        task_name = re.sub(r'\s+(as\s+complete|as\_completed|completed)$', '', task_name, flags=re.IGNORECASE).strip()

        return ActionProposal(
            proposal_id=proposal_id,
            intent_type=ActionIntentType.COMPLETE_TASK,
            title=f"Complete Task: {task_name}",
            description=f"Action proposal to mark task '{task_name}' as completed.",
            parameters={
                "task_name": task_name
            },
            workspace_id=str(workspace_id) if workspace_id else None,
            user_id=str(user_id) if user_id else None,
            confirmation_required=True,
            status=ActionStatus.READY_FOR_CONFIRMATION
        )

    @classmethod
    def _extract_create_reminder_proposal(
        cls,
        query: str,
        proposal_id: str,
        workspace_id: Optional[UUID],
        user_id: Optional[UUID]
    ) -> ActionProposal:
        clean_query = query.rstrip('.!? ').strip()

        # Parse time expression
        time_match = re.search(r'\b(in\s+\d+\s+(?:minutes?|mins?|hours?|hrs?|days?)|tomorrow(?:\s+morning|\s+evening|\s+afternoon|\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?|on\s+[A-Za-z]+\s+\d+|later|next week)\b', clean_query, re.IGNORECASE)
        time_str = time_match.group(0) if time_match else None

        # Clean reminder text
        rem_text = clean_query
        rem_text = re.sub(r'^(can you\s+)?(please\s+)?(remind me|set a reminder|create a reminder|don\'t let me forget|don\'t forget|i need a reminder|set me a reminder)\s*', '', rem_text, flags=re.IGNORECASE).strip()
        if time_str:
            rem_text = re.sub(r'\b' + re.escape(time_str) + r'\b', '', rem_text, flags=re.IGNORECASE).strip()
        rem_text = re.sub(r'^(to|about|for|that|the)\b\s*', '', rem_text, flags=re.IGNORECASE).strip()
        rem_text = re.sub(r'\s+(tomorrow|later|next week)$', '', rem_text, flags=re.IGNORECASE).strip()

        generic_reminders = {"", "reminder", "a reminder", "me", "this", "about this", "later", "tomorrow", "for tomorrow", "for"}

        if not rem_text or rem_text.lower() in generic_reminders:
            return ActionProposal(
                proposal_id=proposal_id,
                intent_type=ActionIntentType.CREATE_REMINDER,
                title="Create Reminder",
                parameters={"time_str": time_str or "tomorrow"},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=False,
                status=ActionStatus.NEEDS_CLARIFICATION,
                clarification_prompt="What would you like me to remind you about?"
            )

        clean_text = rem_text[0].upper() + rem_text[1:] if len(rem_text) > 0 else rem_text

        if not time_str:
            return ActionProposal(
                proposal_id=proposal_id,
                intent_type=ActionIntentType.CREATE_REMINDER,
                title="Create Reminder",
                description="Reminder missing schedule.",
                parameters={"reminder_text": clean_text, "missing": ["time_str"]},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=False,
                status=ActionStatus.NEEDS_CLARIFICATION,
                clarification_prompt="Sure. When should I remind you?"
            )

        return ActionProposal(
            proposal_id=proposal_id,
            intent_type=ActionIntentType.CREATE_REMINDER,
            title=f"Set Reminder: {clean_text} ({time_str})",
            description=f"Action proposal to schedule reminder for {time_str}.",
            parameters={
                "reminder_text": clean_text,
                "time_str": time_str
            },
            workspace_id=str(workspace_id) if workspace_id else None,
            user_id=str(user_id) if user_id else None,
            confirmation_required=True,
            status=ActionStatus.READY_FOR_CONFIRMATION
        )

    @classmethod
    def _extract_cancel_reminder_proposal(
        cls,
        query: str,
        proposal_id: str,
        workspace_id: Optional[UUID],
        user_id: Optional[UUID]
    ) -> ActionProposal:
        keyword_match = re.sub(r'^(please\s+)?(cancel|delete)\s+(my|the)?\s*reminder\s*(about|for)?\s*', '', query, flags=re.IGNORECASE).rstrip('.')
        keyword = keyword_match.strip()

        return ActionProposal(
            proposal_id=proposal_id,
            intent_type=ActionIntentType.CREATE_REMINDER,
            title=f"Cancel Reminder: {keyword}",
            description=f"Action proposal to cancel scheduled reminder matching '{keyword}'.",
            parameters={
                "keyword": keyword,
                "is_cancel_action": True
            },
            workspace_id=str(workspace_id) if workspace_id else None,
            user_id=str(user_id) if user_id else None,
            confirmation_required=True,
            status=ActionStatus.READY_FOR_CONFIRMATION
        )

    @classmethod
    def _extract_send_message_proposal(
        cls,
        query: str,
        proposal_id: str,
        workspace_id: Optional[UUID],
        user_id: Optional[UUID],
        resolved_context: Optional[Dict[str, Any]] = None
    ) -> ActionProposal:
        clean_query = query.rstrip('.!? ').strip()

        # 1. Group / Team Recipient Patterns
        group_match = re.search(r'\b(tell|message|inform|send a message to|send message to|send DM to)\s+(the\s+team|the\s+devs|the\s+developers|the\s+group|everyone|the\s+channel)\b', clean_query, re.IGNORECASE)
        recipient = None
        raw_rec_token = None

        if group_match:
            recipient = group_match.group(2).strip()
            raw_rec_token = recipient

        # 2. Individual / Multi-word / Named Recipient Patterns
        if not recipient:
            m_rec = re.search(r'\b(?:message|send\s+(?:a\s+)?(?:dm|message)\s+to|tell|let|inform|ping)\s+([A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+)?|[a-z0-9]+)\b', clean_query, re.IGNORECASE)
            if m_rec:
                cand = m_rec.group(1).strip()
                tokens = cand.split()
                connectors = {"the", "that", "to", "saying", "is", "a", "an", "on", "for", "in", "at", "by", "from", "message", "dm", "direct", "us", "someone", "know", "him", "her", "them", "it", "me"}
                valid_tokens = []
                for t in tokens:
                    if t.lower() in connectors:
                        break
                    valid_tokens.append(t)
                if valid_tokens:
                    recipient = " ".join(valid_tokens)
                    raw_rec_token = recipient

        # 3. Contextual / Pronoun Resolution ("him", "her", "them", "the project lead")
        if not recipient or recipient.lower() in ["him", "her", "them"]:
            if resolved_context and resolved_context.get("last_mentioned_user"):
                recipient = resolved_context["last_mentioned_user"]
            elif resolved_context and resolved_context.get("last_speaker"):
                recipient = resolved_context["last_speaker"]

        if not recipient:
            return ActionProposal(
                proposal_id=proposal_id,
                intent_type=ActionIntentType.SEND_DIRECT_MESSAGE,
                title="Send Direct Message",
                parameters={},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=False,
                status=ActionStatus.NEEDS_CLARIFICATION,
                clarification_prompt="Who would you like to send the message to?"
            )

        # 4. Extract Message Body
        msg_body = ""
        target_token = raw_rec_token or recipient
        body_pattern = rf'\b(?:{re.escape(target_token)}|him|her|them)\b\s*(?::\s*|that\s+|saying\s+|a\s+message\s+saying\s+|a\s+message\s+that\s+|a\s+dm\s+saying\s+|know\s+that\s+|know\s+)?(.*)'
        m_body = re.search(body_pattern, clean_query, re.IGNORECASE)

        if m_body and m_body.group(1).strip():
            raw_body = m_body.group(1).strip()
            msg_body = re.sub(r'^(?:that|saying|a message saying|a message that|a dm saying|know that)\s+', '', raw_body, flags=re.IGNORECASE).strip()
            msg_body = re.sub(r'^(?::\s*|"\s*|\'\s*)', '', msg_body).strip(' "\'')

        if not msg_body or msg_body.lower() in ["message", "a message", "a dm", "dm", "a dm."]:
            return ActionProposal(
                proposal_id=proposal_id,
                intent_type=ActionIntentType.SEND_DIRECT_MESSAGE,
                title=f"Send Message to {recipient.title()}",
                parameters={"recipient_name": recipient.title()},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=False,
                status=ActionStatus.NEEDS_CLARIFICATION,
                clarification_prompt=f"What would you like me to tell {recipient.title()}?"
            )

        clean_rec = recipient.title() if not recipient.lower().startswith("the ") else recipient
        clean_msg = msg_body[0].upper() + msg_body[1:] if len(msg_body) > 0 else msg_body

        return ActionProposal(
            proposal_id=proposal_id,
            intent_type=ActionIntentType.SEND_DIRECT_MESSAGE,
            title=f"Send Message to {clean_rec}: '{clean_msg}'",
            description=f"Action proposal to send direct message to {clean_rec}.",
            parameters={
                "recipient_name": clean_rec,
                "message_body": clean_msg
            },
            workspace_id=str(workspace_id) if workspace_id else None,
            user_id=str(user_id) if user_id else None,
            confirmation_required=True,
            status=ActionStatus.READY_FOR_CONFIRMATION
        )

    @classmethod
    def _extract_create_automation_proposal(
        cls,
        query: str,
        proposal_id: str,
        workspace_id: Optional[UUID],
        user_id: Optional[UUID],
        resolved_context: Optional[Dict[str, Any]] = None
    ) -> ActionProposal:
        q_lower = query.lower()

        # 1. Block Destructive Scheduled Actions for Safety
        if any(w in q_lower for w in ["delete", "remove", "drop", "destroy", "wipe", "clear"]) and any(w in q_lower for w in ["task", "tasks", "user", "users", "file", "files", "project", "document", "documents"]):
            return ActionProposal(
                proposal_id=proposal_id,
                intent_type=ActionIntentType.CREATE_AUTOMATION,
                title="Blocked Destructive Action",
                description="Destructive actions (such as recurring deletion) are disabled for safety.",
                parameters={"is_blocked": True},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=False,
                status=ActionStatus.FAILED,
                clarification_prompt="I can't schedule destructive actions through MindMesh."
            )

        schedule_type = "DAILY"
        day_of_week = None
        has_explicit_schedule = False

        if "every monday" in q_lower or "on monday" in q_lower:
            schedule_type = "WEEKLY"; day_of_week = "Monday"; has_explicit_schedule = True
        elif "every tuesday" in q_lower or "on tuesday" in q_lower:
            schedule_type = "WEEKLY"; day_of_week = "Tuesday"; has_explicit_schedule = True
        elif "every wednesday" in q_lower or "on wednesday" in q_lower:
            schedule_type = "WEEKLY"; day_of_week = "Wednesday"; has_explicit_schedule = True
        elif "every thursday" in q_lower or "on thursday" in q_lower:
            schedule_type = "WEEKLY"; day_of_week = "Thursday"; has_explicit_schedule = True
        elif "every friday" in q_lower or "on friday" in q_lower:
            schedule_type = "WEEKLY"; day_of_week = "Friday"; has_explicit_schedule = True
        elif "every saturday" in q_lower or "on saturday" in q_lower:
            schedule_type = "WEEKLY"; day_of_week = "Saturday"; has_explicit_schedule = True
        elif "every sunday" in q_lower or "on sunday" in q_lower:
            schedule_type = "WEEKLY"; day_of_week = "Sunday"; has_explicit_schedule = True
        elif "every weekday" in q_lower:
            schedule_type = "WEEKDAYS"; has_explicit_schedule = True
        elif "every month" in q_lower or "monthly" in q_lower:
            schedule_type = "MONTHLY"; has_explicit_schedule = True
        elif "every day" in q_lower or "daily" in q_lower:
            schedule_type = "DAILY"; has_explicit_schedule = True
        elif "tomorrow" in q_lower or "next week" in q_lower or "in " in q_lower:
            schedule_type = "ONE_TIME"; has_explicit_schedule = True

        time_match = re.search(r'\bat\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', q_lower)
        time_str = time_match.group(1).upper() if time_match else None

        # 2. Clarification for Ambiguous / Missing Time
        if has_explicit_schedule and not time_str and schedule_type != "ONE_TIME":
            day_text = day_of_week or schedule_type.title()
            return ActionProposal(
                proposal_id=proposal_id,
                intent_type=ActionIntentType.CREATE_AUTOMATION,
                title="Create Automation",
                parameters={"schedule_type": schedule_type, "day_of_week": day_of_week},
                workspace_id=str(workspace_id) if workspace_id else None,
                user_id=str(user_id) if user_id else None,
                confirmation_required=False,
                status=ActionStatus.NEEDS_CLARIFICATION,
                clarification_prompt=f"What time on {day_text} should I set for this automation?"
            )

        if not time_str:
            time_str = "9:00 AM"

        # 3. Resolve Inner Action Payload
        if any(w in q_lower for w in ["message", "send", "tell"]):
            inner_prop = cls._extract_send_message_proposal(query, proposal_id, workspace_id, user_id, resolved_context=resolved_context)
            action_type = "SEND_DIRECT_MESSAGE"
            action_payload = inner_prop.parameters
            auto_name = f"Scheduled DM to {action_payload.get('recipient_name', 'Workspace Member')}"
        elif "task" in q_lower and any(w in q_lower for w in ["create", "add", "make", "new"]):
            inner_prop = cls._extract_create_task_proposal(query, proposal_id, workspace_id, user_id, resolved_context=resolved_context)
            action_type = "CREATE_TASK"
            action_payload = inner_prop.parameters
            auto_name = f"Scheduled Task: {action_payload.get('title', 'Task')}"
        else:
            inner_prop = cls._extract_create_reminder_proposal(query, proposal_id, workspace_id, user_id)
            action_type = "CREATE_REMINDER"
            action_payload = inner_prop.parameters
            auto_name = f"Scheduled Reminder: {action_payload.get('reminder_text', 'Reminder')}"

        sched_label = f"Every {day_of_week}" if day_of_week else schedule_type.title()

        return ActionProposal(
            proposal_id=proposal_id,
            intent_type=ActionIntentType.CREATE_AUTOMATION,
            title=f"Create Automation: {auto_name}",
            description=f"Action proposal to schedule '{auto_name}' ({sched_label} at {time_str}).",
            parameters={
                "name": auto_name,
                "action_type": action_type,
                "action_payload": action_payload,
                "schedule_type": schedule_type,
                "day_of_week": day_of_week,
                "time_str": time_str,
                "recurrence_rule": f"every_{day_of_week.lower()}" if day_of_week else schedule_type.lower()
            },
            workspace_id=str(workspace_id) if workspace_id else None,
            user_id=str(user_id) if user_id else None,
            confirmation_required=True,
            status=ActionStatus.READY_FOR_CONFIRMATION
        )
