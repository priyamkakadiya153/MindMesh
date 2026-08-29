import re
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID

from app.actions.candidate import (
    ActionCandidate,
    ProvenanceContext,
    IntentCategory,
    ActionType,
    ConfidenceLevel,
    CandidateStatus
)

logger = logging.getLogger(__name__)

class ProactiveDetectionEngine:
    """
    AUTO-01 Action & Intent Foundation Engine.
    Semantically understands normal messages across Direct Messages, Group Chat,
    AI Chat, Project Channels, and Workspace Conversations.
    
    Produces structured ActionCandidate representations without taking downstream execution.
    """

    ACTION_VERBS = [
        "finish", "finished", "review", "send", "prepare", "update", "complete", "completed", "submit",
        "draft", "deploy", "test", "fix", "write", "create", "build", "check",
        "upload", "deliver", "organize", "schedule", "implement", "do", "handle",
        "take care of", "get done", "make sure", "inspect", "verify"
    ]

    PAST_TENSE_INDICATORS = [
        "was completed", "started in", "was done", "completed last", "finished last",
        "was moved", "were discussed", "discussed yesterday", "completed on"
    ]

    COMPLETION_PATTERNS = [
        r"\b(i|we|i've|have)\s+(completed|finished|submitted|sent|done|fixed|updated|built|resolved)\b",
        r"\b(i|i've)\s+already\s+(completed|finished|submitted|sent|done|fixed)\b",
        r"\b(completed|finished|submitted|sent|done|fixed)\s+(my|the|this|that|our)\s+(task|report|doc|docs|documentation|deliverable|issue|ticket|part|work)\b",
        r"\b(the|this)\s+(task|report|doc|docs|documentation|deliverable|issue|ticket|part)\s+is\s+(completed|done|finished|submitted|sent|fixed)\b",
        r"^(done|finished|completed|i've completed everything|i completed everything)\.?$"
    ]

    NON_ACTION_EXPRESSIONS = [
        "our meeting is", "the meeting is", "started in", "was completed",
        "happened on", "deadline might be", "might be next", "meeting was",
        "discussed yesterday", "deadline was moved"
    ]

    LOW_CONFIDENCE_INDICATORS = [
        "maybe", "sometime", "probably", "not sure", "might be", "perhaps",
        "think we could", "possibly"
    ]

    DAYS_MAP = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }

    @staticmethod
    def _boolean_equal(val1: Optional[str], val2: Optional[str]) -> bool:
        if not val1 or not val2:
            return False
        return val1.strip().lower() == val2.strip().lower()

    @classmethod
    def detect_candidate_action(
        cls,
        text: str,
        history: Optional[List[Dict[str, Any]]] = None,
        source_type: str = "DIRECT_MESSAGE",
        conversation_id: str = "",
        message_id: Optional[str] = None,
        sender_id: Optional[str] = None,
        sender_name: Optional[str] = None,
        current_user_id: Optional[str] = None,
        current_user_name: Optional[str] = None,
        workspace_id: Optional[str] = None,
        user_timezone_offset_hours: float = 5.5,
        message_timestamp: Optional[datetime] = None
    ) -> ActionCandidate:
        """
        Analyzes message text and conversation history to produce a structured, role-aware ActionCandidate
        from the point of view (POV) of current_user_id / current_user_name.
        Does NOT execute any tasks, reminders, automations, or notifications.
        """
        from app.actions.candidate import UserResponsibilityRole
        now = message_timestamp or datetime.now(timezone.utc)
        provenance = ProvenanceContext(
            source_type=source_type,
            conversation_id=conversation_id,
            message_id=message_id,
            sender_id=sender_id,
            sender_name=sender_name,
            workspace_id=workspace_id,
            timestamp=now
        )

        no_action_candidate = ActionCandidate(
            source=provenance,
            intent=IntentCategory.NO_ACTION,
            action_type=ActionType.NO_ACTION,
            confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
            personal_relevance=ConfidenceLevel.LOW,
            status=CandidateStatus.DETECTED
        )

        if not text or not text.strip():
            return no_action_candidate

        raw_text = text.strip()
        lower_text = raw_text.lower()

        # 1. Past Tense / Historical Completed Statement Filtering
        for past in cls.PAST_TENSE_INDICATORS:
            if past in lower_text:
                return ActionCandidate(
                    source=provenance,
                    intent=IntentCategory.INFORMATION_ONLY,
                    action_type=ActionType.NO_ACTION,
                    candidate_type="NO_ACTION",
                    subject=raw_text,
                    description=f"Information statement: {raw_text}",
                    confidence=0.20,
                    confidence_level=ConfidenceLevel.LOW,
                    personal_relevance=ConfidenceLevel.LOW,
                    status=CandidateStatus.DETECTED
                )

        # Topic Change Cutoff Check in History
        cleaned_history = cls._clean_history_with_topic_cutoff(history)

        # 2. Completion Statement Detection
        is_completion_statement = any(re.search(pat, lower_text) for pat in cls.COMPLETION_PATTERNS)
        
        # 2. Check for Non-Action Information Statements
        is_info_statement = any(non_act in lower_text for non_act in cls.NON_ACTION_EXPRESSIONS)
        has_explicit_verb = any(re.search(rf"\b{verb}\b", lower_text) for verb in cls.ACTION_VERBS)
        has_request_keyword = any(k in lower_text for k in ["please", "can you", "need to", "got to", "have to", "i'll", "i've got", "let's", "make sure", "don't forget", "don't let me forget", "remind", "should", "could you"])

        if is_info_statement and not has_explicit_verb and not has_request_keyword and not is_completion_statement:
            return ActionCandidate(
                source=provenance,
                intent=IntentCategory.INFORMATION_ONLY,
                action_type=ActionType.NO_ACTION,
                subject=raw_text,
                description=f"Information statement: {raw_text}",
                confidence=0.30,
                confidence_level=ConfidenceLevel.LOW,
                personal_relevance=ConfidenceLevel.LOW,
                status=CandidateStatus.DETECTED
            )

        # 3. Extract Deadline Expression & Normalized Datetime
        deadline_str, normalized_date = cls._extract_deadline(lower_text, now, user_timezone_offset_hours)

        if deadline_str and not has_explicit_verb and not has_request_keyword and not cleaned_history and not is_completion_statement:
            return ActionCandidate(
                source=provenance,
                intent=IntentCategory.INFORMATION_ONLY,
                action_type=ActionType.NO_ACTION,
                subject=raw_text,
                description=f"Date information statement: {raw_text}",
                deadline=deadline_str,
                normalized_deadline=normalized_date,
                confidence=0.30,
                confidence_level=ConfidenceLevel.LOW,
                personal_relevance=ConfidenceLevel.LOW,
                status=CandidateStatus.DETECTED
            )

        # 4. Extract Assignee & Speaker Responsibility
        assignee_name, is_speaker_commitment = cls._detect_assignee(raw_text, lower_text, sender_name)

        # 5. Extract Action Subject (Direct or Contextual / Pronoun Resolution)
        action_title, is_contextual, extracted_intent = cls._extract_action_title_and_intent(
            raw_text, lower_text, cleaned_history, sender_name
        )

        if not action_title and is_completion_statement:
            # Fallback action title for completion statement if pronoun e.g. "I completed my part"
            action_title = raw_text.capitalize()

        if not action_title:
            return no_action_candidate

        # 6. Role & POV Evaluation
        evaluating_user_name = current_user_name or "Current user"
        speaking_user_name = sender_name or "Sender"

        # Determine roles
        is_speaker = cls._boolean_equal(evaluating_user_name, speaking_user_name)
        
        # Is evaluating user explicitly assigned or addressed?
        is_evaluating_user_assignee = False
        if assignee_name:
            if cls._boolean_equal(assignee_name, evaluating_user_name) or (assignee_name == "Current speaker" and is_speaker):
                is_evaluating_user_assignee = True
        elif is_speaker_commitment and is_speaker:
            is_evaluating_user_assignee = True

        # Handle Completion Statement Logic
        if is_completion_statement:
            if is_speaker or is_evaluating_user_assignee:
                # Member POV (Speaker): Completion recognized! Do NOT generate a new task request for speaker.
                clean_title = action_title.strip().lower()
                hash_input = f"{workspace_id or ''}:{conversation_id}:{clean_title}:completion:{current_user_id or evaluating_user_name}:COMPLETION"
                action_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
                return ActionCandidate(
                    source=provenance,
                    intent=IntentCategory.COMPLETION_SIGNAL,
                    action_type=ActionType.COMPLETION,
                    candidate_type="COMPLETION",
                    user_role=UserResponsibilityRole.ASSIGNEE,
                    subject=action_title,
                    description=f"Completion recognized from message: \"{raw_text}\"",
                    deadline=deadline_str,
                    normalized_deadline=normalized_date,
                    assignee=speaking_user_name,
                    assignee_name=speaking_user_name,
                    requester=None,
                    confidence=0.90,
                    confidence_level=ConfidenceLevel.LOW, # Low confidence so it won't create a new task
                    requires_user_confirmation=False,
                    personal_relevance=ConfidenceLevel.LOW, # Low relevance so no popup task created
                    status=CandidateStatus.DETECTED,
                    detected_action_hash=action_hash,
                    provenance={
                        "source_type": source_type,
                        "conversation_id": conversation_id,
                        "message_id": message_id,
                        "sender_id": sender_id,
                        "sender_name": sender_name,
                        "timestamp": now.isoformat()
                    }
                )
            else:
                # Leader POV: Member reported completing deliverable! Offer a REVIEW / FOLLOW_UP candidate to Leader.
                review_subject = f"Review {action_title} completed by {speaking_user_name}"
                clean_title = review_subject.strip().lower()
                hash_input = f"{workspace_id or ''}:{conversation_id}:{clean_title}:review:{current_user_id or evaluating_user_name}:REVIEW"
                action_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

                return ActionCandidate(
                    source=provenance,
                    intent=IntentCategory.REVIEW_REQUEST,
                    action_type=ActionType.REVIEW,
                    candidate_type="REVIEW",
                    user_role=UserResponsibilityRole.REQUESTER,
                    subject=review_subject,
                    description=f"Member {speaking_user_name} reported completing: \"{raw_text}\"",
                    deadline=deadline_str or "Today",
                    normalized_deadline=normalized_date or now,
                    assignee=evaluating_user_name,
                    assignee_name=evaluating_user_name,
                    requester=speaking_user_name,
                    confidence=0.88,
                    confidence_level=ConfidenceLevel.HIGH,
                    requires_user_confirmation=True,
                    personal_relevance=ConfidenceLevel.HIGH,
                    status=CandidateStatus.DETECTED,
                    detected_action_hash=action_hash,
                    provenance={
                        "source_type": source_type,
                        "conversation_id": conversation_id,
                        "message_id": message_id,
                        "sender_id": sender_id,
                        "sender_name": sender_name,
                        "timestamp": now.isoformat()
                    }
                )

        # 7. Non-Completion Intent & Dual-POV Candidate Generation
        if not extracted_intent:
            if "remind me" in lower_text or "don't forget" in lower_text:
                extracted_intent = IntentCategory.REMINDER_INTENT
            elif is_speaker_commitment:
                extracted_intent = IntentCategory.COMMITMENT
            elif "please" in lower_text or "can you" in lower_text or "could you" in lower_text:
                extracted_intent = IntentCategory.TASK_REQUEST if not assignee_name else IntentCategory.REQUEST_TO_PERSON
            elif "let's" in lower_text or "we need to" in lower_text:
                extracted_intent = IntentCategory.DELIVERABLE
            elif deadline_str:
                extracted_intent = IntentCategory.DEADLINE
            else:
                extracted_intent = IntentCategory.FOLLOW_UP

        # Evaluate current user role for standard requests/commitments
        if is_speaker:
            if is_speaker_commitment:
                user_role = UserResponsibilityRole.ASSIGNEE
                candidate_type = "CREATE_REMINDER" if extracted_intent == IntentCategory.REMINDER_INTENT else "CREATE_TASK"
            else:
                user_role = UserResponsibilityRole.REQUESTER
                candidate_type = "FOLLOW_UP"
        else:
            if assignee_name and cls._boolean_equal(assignee_name, evaluating_user_name):
                user_role = UserResponsibilityRole.ASSIGNEE
                candidate_type = "CREATE_TASK"
            elif source_type == "DIRECT_MESSAGE":
                user_role = UserResponsibilityRole.ASSIGNEE
                candidate_type = "CREATE_TASK"
            elif assignee_name and not cls._boolean_equal(assignee_name, evaluating_user_name):
                user_role = UserResponsibilityRole.OBSERVER
                candidate_type = "NO_ACTION"
            else:
                user_role = UserResponsibilityRole.OBSERVER
                candidate_type = "NO_ACTION"

        # Action Type Mapping
        action_type = ActionType.TASK
        if candidate_type == "CREATE_REMINDER":
            action_type = ActionType.REMINDER
        elif candidate_type == "FOLLOW_UP":
            action_type = ActionType.FOLLOW_UP
        elif candidate_type == "REVIEW":
            action_type = ActionType.REVIEW

        # Confidence Classification
        has_speculative = any(w in lower_text for w in ["maybe", "not sure", "sometime", "might be", "perhaps"])

        if user_role == UserResponsibilityRole.OBSERVER:
            confidence = 0.20
            confidence_level = ConfidenceLevel.LOW
            personal_relevance = ConfidenceLevel.LOW
        elif has_speculative and not (has_explicit_verb and deadline_str):
            confidence = 0.45
            confidence_level = ConfidenceLevel.LOW
            personal_relevance = ConfidenceLevel.LOW
        elif deadline_str and (has_explicit_verb or is_contextual or has_request_keyword):
            confidence = 0.92
            confidence_level = ConfidenceLevel.HIGH
            personal_relevance = ConfidenceLevel.HIGH
        elif has_explicit_verb or has_request_keyword or is_speaker_commitment or is_contextual:
            confidence = 0.75
            confidence_level = ConfidenceLevel.MEDIUM
            personal_relevance = ConfidenceLevel.HIGH if user_role == UserResponsibilityRole.ASSIGNEE else ConfidenceLevel.MEDIUM
        else:
            confidence = 0.50
            confidence_level = ConfidenceLevel.LOW
            personal_relevance = ConfidenceLevel.LOW

        # Generate role-appropriate title
        final_title = action_title
        if user_role == UserResponsibilityRole.REQUESTER and candidate_type == "FOLLOW_UP":
            target_person = assignee_name or (speaking_user_name if not is_speaker else "team member")
            final_title = f"Follow up on {action_title} from {target_person}"

        clean_title = final_title.strip().lower()
        clean_deadline = (deadline_str or "").strip().lower()
        hash_input = f"{workspace_id or ''}:{conversation_id}:{clean_title}:{clean_deadline}:{current_user_id or evaluating_user_name}:{candidate_type}"
        action_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        return ActionCandidate(
            source=provenance,
            intent=extracted_intent,
            action_type=action_type,
            candidate_type=candidate_type,
            user_role=user_role,
            subject=final_title,
            description=f"Detected from message: \"{raw_text}\"",
            deadline=deadline_str,
            normalized_deadline=normalized_date,
            timezone="Asia/Kolkata" if user_timezone_offset_hours == 5.5 else ("UTC" if user_timezone_offset_hours == 0 else f"UTC+{user_timezone_offset_hours}"),
            assignee=assignee_name or (evaluating_user_name if user_role == UserResponsibilityRole.ASSIGNEE else speaking_user_name),
            assignee_name=assignee_name or (evaluating_user_name if user_role == UserResponsibilityRole.ASSIGNEE else speaking_user_name),
            requester=speaking_user_name if not is_speaker else evaluating_user_name,
            confidence=confidence,
            confidence_level=confidence_level,
            requires_user_confirmation=True,
            personal_relevance=personal_relevance,
            status=CandidateStatus.DETECTED,
            detected_action_hash=action_hash,
            provenance={
                "source_type": source_type,
                "conversation_id": conversation_id,
                "message_id": message_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "timestamp": now.isoformat()
            }
        )

    @classmethod
    def _clean_history_with_topic_cutoff(
        cls, history: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Filter recent history and stop at topic changes."""
        if not history:
            return []

        recent = history[-5:]
        cleaned = []
        
        topic_change_patterns = [
            r"\b(anyway|by the way|on another note|speaking of which|how was|how were)\b"
        ]

        for msg in recent:
            content = msg.get("content", "").lower()
            if any(re.search(pat, content) for pat in topic_change_patterns):
                # Topic changed at this message; discard prior history context
                cleaned = []
            else:
                cleaned.append(msg)
        return cleaned

    @classmethod
    def _detect_assignee(
        cls, raw_text: str, lower_text: str, sender_name: Optional[str]
    ) -> Tuple[Optional[str], bool]:
        """Detects whether speaker is committing or another person is assigned."""
        is_speaker_commitment = bool(re.search(r"\b(i'll|i will|i'm going to|i need to|let me)\b", lower_text))

        # Check for explicit named assignee in request: "Rahul, can you..." or "Priyam will update..."
        name_match = re.match(r"^([A-Z][a-z]+)[,\s]+(please|can you|could you|you need to|will|should)", raw_text)
        if name_match:
            return name_match.group(1).capitalize(), False

        # Pattern: "Priyam will update..."
        statement_match = re.search(r"\b([A-Z][a-z]+)\s+(will|is going to|can|should)\s+", raw_text)
        if statement_match:
            candidate_name = statement_match.group(1).capitalize()
            if candidate_name.lower() not in ["the", "we", "i", "you", "they", "our"]:
                return candidate_name, False

        if is_speaker_commitment and sender_name:
            return sender_name, True
        elif is_speaker_commitment:
            return "Current speaker", True

        return None, False

    @classmethod
    def _extract_deadline(
        cls, lower_text: str, now: datetime, tz_offset_hours: float = 5.5
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """
        Extracts human deadline string and calculates normalized datetime with Asia/Kolkata (IST) timezone support.
        Resolves relative date phrases ("tomorrow", "today", "day after tomorrow", "in 3 days", "by Friday")
        relative to the message reference timestamp (now), and returns a stable absolute date string (e.g. "21 Aug 2026").
        Does NOT invent artificial time for tasks unless explicitly specified.
        """
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        if now.tzinfo is None:
            ref_utc = now.replace(tzinfo=timezone.utc)
        else:
            ref_utc = now.astimezone(timezone.utc)

        ref_ist = ref_utc.astimezone(ist_tz)
        ref_date = ref_ist.date()

        patterns = [
            (r"\b(by|before|until|due|deadline is)\s+(tomorrow's client meeting|tomorrow morning|tomorrow afternoon|tomorrow evening|tomorrow at \d+[\:\d+]*\s*(?:am|pm)?|tomorrow|day after tomorrow|today|yesterday)\b", 2),
            (r"\b(by|before|until|due|deadline is)\s+(the end of (?:this |the )?week|end of (?:this |the )?week|end of day|eod)\b", 2),
            (r"\b(by|before|until|due|deadline is)\s+(next (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|this (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b", 2),
            (r"\b(within|in)\s+(\d+|two|three|four|five|six|seven|a)\s+(days|day|week|weeks)\b", 0),
            (r"\b(before|by)\s+(the client call|the meeting|the demo)\b", 0)
        ]

        raw_deadline = None
        for pattern, grp in patterns:
            match = re.search(pattern, lower_text)
            if match:
                raw_deadline = match.group(grp) if grp > 0 else match.group(0)
                break

        if not raw_deadline:
            if "day after tomorrow" in lower_text:
                raw_deadline = "day after tomorrow"
            elif "by tomorrow" in lower_text or "before tomorrow" in lower_text or ("tomorrow" in lower_text and ("send" in lower_text or "finish" in lower_text or "deck" in lower_text or "ppt" in lower_text or "complete" in lower_text or "report" in lower_text or "doc" in lower_text)):
                raw_deadline = "tomorrow"
            elif "today" in lower_text:
                raw_deadline = "today"
            elif "yesterday" in lower_text:
                raw_deadline = "yesterday"
            elif "by friday" in lower_text or "before friday" in lower_text or "this friday" in lower_text or "ready by friday" in lower_text:
                raw_deadline = "Friday"
            elif "next friday" in lower_text:
                raw_deadline = "next Friday"
            elif "next monday" in lower_text or "by monday" in lower_text or "before monday" in lower_text:
                raw_deadline = "Monday"
            elif "by eod" in lower_text or "by end of day" in lower_text or "end of day" in lower_text:
                raw_deadline = "EOD"
            elif "this week" in lower_text:
                raw_deadline = "This week"
            elif "next week" in lower_text:
                raw_deadline = "Next week"
            elif "this weekend" in lower_text:
                raw_deadline = "This weekend"

        if not raw_deadline:
            return None, None

        deadline_lower = raw_deadline.lower()
        target_date = ref_date
        explicit_time_str = None
        has_explicit_time = False

        if "day after tomorrow" in deadline_lower:
            target_date = ref_date + timedelta(days=2)
        elif "tomorrow" in deadline_lower:
            target_date = ref_date + timedelta(days=1)
        elif "today" in deadline_lower:
            target_date = ref_date
        elif "yesterday" in deadline_lower:
            target_date = ref_date - timedelta(days=1)
        elif "eod" in deadline_lower or "end of day" in deadline_lower:
            target_date = ref_date
            explicit_time_str = "EOD"
            has_explicit_time = True
        else:
            num_match = re.search(r"(?:in|within)\s+(\d+|two|three|four|five|six|seven|a)\s+(days|day|week|weeks)", deadline_lower)
            if num_match:
                val_str = num_match.group(1)
                unit_str = num_match.group(2)
                num_val = 1
                if val_str.isdigit():
                    num_val = int(val_str)
                elif val_str == "two": num_val = 2
                elif val_str == "three": num_val = 3
                elif val_str == "four": num_val = 4
                elif val_str == "five": num_val = 5
                elif val_str == "six": num_val = 6
                elif val_str == "seven": num_val = 7

                if "week" in unit_str:
                    target_date = ref_date + timedelta(weeks=num_val)
                else:
                    target_date = ref_date + timedelta(days=num_val)
            else:
                for day_name, day_num in cls.DAYS_MAP.items():
                    if day_name in deadline_lower:
                        days_ahead = day_num - ref_date.weekday()
                        if days_ahead <= 0 or "next" in deadline_lower:
                            days_ahead += 7
                        target_date = ref_date + timedelta(days=days_ahead)
                        break

        if "morning" in lower_text or "morning" in deadline_lower:
            explicit_time_str = "Morning"
            has_explicit_time = True
        elif "afternoon" in lower_text or "afternoon" in deadline_lower:
            explicit_time_str = "Afternoon"
            has_explicit_time = True
        elif "evening" in lower_text or "evening" in deadline_lower:
            explicit_time_str = "Evening"
            has_explicit_time = True

        time_at_match = re.search(r"\bat\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", lower_text)
        if time_at_match:
            explicit_time_str = time_at_match.group(1).upper()
            has_explicit_time = True

        display_deadline = raw_deadline.capitalize()
        if "client meeting" in lower_text:
            display_deadline = "Before tomorrow's client meeting" if "tomorrow" in lower_text else "Before client meeting"
        elif "client call" in lower_text:
            display_deadline = "Before the client call"
        elif "demo" in lower_text:
            display_deadline = "Before the demo"

        norm_dt = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, tzinfo=ist_tz).astimezone(timezone.utc)

        return display_deadline, norm_dt

    @classmethod
    def _extract_action_title_and_intent(
        cls,
        raw_text: str,
        lower_text: str,
        history: Optional[List[Dict[str, Any]]],
        sender_name: Optional[str]
    ) -> Tuple[Optional[str], bool, Optional[IntentCategory]]:
        """
        Extracts action title directly or resolves pronouns ("it", "this", "that", "the report")
        from conversation history.
        """
        is_pronoun_followup = bool(re.search(r"\b(do it|have it ready|get it done|finish it|finished it|completed it|sent it|done with it|take care of it)\b", lower_text))

        if (is_pronoun_followup or "finished it" in lower_text or "completed it" in lower_text) and history:
            # Search recent messages in history for explicit action subject
            for msg in reversed(history):
                prev_text = msg.get("content", "")
                prev_lower = prev_text.lower()
                action = cls._parse_direct_action_phrase(prev_text, prev_lower)
                if action:
                    return action, True, IntentCategory.COMMITMENT

        direct_action = cls._parse_direct_action_phrase(raw_text, lower_text)
        if direct_action:
            return direct_action, False, None

        return None, False, None

    @classmethod
    def _parse_direct_action_phrase(cls, raw_text: str, lower_text: str) -> Optional[str]:
        """Parses an explicit action phrase from a single text line."""
        clean_text = raw_text.rstrip(".,!?")
        patterns = [
            r"(?:please|can you|could you|make sure to|don't forget to|someone needs to|can someone make sure|can someone make sure that|make sure)\s+([a-z0-9\s,\-_]+?)(?:\s+(?:by|before|until|due|within|next|this|tomorrow|eod)|$)",
            r"(?:i'll|i will|i'm going to|i need to|we need to|we should|i should|i should probably|we'll|let's|i've got to|i've got to get)\s+([a-z0-9\s,\-_]+?)(?:\s+(?:by|before|until|due|within|next|this|tomorrow|eod)|$)",
            r"(?:don't let me forget about|don't forget about|remind me about|remind me to|make sure about|take care of)\s+([a-z0-9\s,\-_]+?)(?:\s+(?:by|before|until|due|within|next|this|tomorrow|eod)|$)"
        ]

        for pat in patterns:
            match = re.search(pat, clean_text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                candidate = re.sub(r"\s+(by|before|until|on|at|due)$", "", candidate, flags=re.IGNORECASE)
                candidate = candidate.rstrip(".,!?")
                if len(candidate.split()) >= 1 and not candidate.lower().startswith("do it") and not candidate.lower().startswith("have it"):
                    return candidate.capitalize()

        # Verb search fallback
        words = raw_text.split()
        for i, w in enumerate(words):
            clean_w = w.lower().strip(".,!?")
            if clean_w in cls.ACTION_VERBS:
                phrase = " ".join(words[i:])
                phrase = re.split(r"\b(by|before|until|due|within|next)\b", phrase, flags=re.IGNORECASE)[0].strip()
                phrase = phrase.rstrip(".,!?")
                lower_p = phrase.lower()
                if len(phrase.split()) >= 2 and not lower_p.startswith("do it") and not lower_p.startswith("have it") and not lower_p.startswith("finished it") and not lower_p.startswith("completed it"):
                    return phrase.capitalize()

        return None
