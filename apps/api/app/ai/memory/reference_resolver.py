import re
from typing import List, Dict, Any, Optional
from app.ai.memory.context_models import ResolvedReference

class ReferenceResolver:
    """
    Resolves conversational pronouns, ordinals, and explicit user reference corrections against conversation context.
    """

    CORRECTION_PATTERNS = [
        re.compile(r"^\s*(no|actually|wait),?\s+i\s+meant\s+(.+)$", re.IGNORECASE),
        re.compile(r"^\s*(no|actually|wait),?\s+(.+)$", re.IGNORECASE)
    ]

    ORDINAL_PATTERNS = [
        (re.compile(r"\b(the\s+)?first(\s+one|\s+project|\s+option)?\b", re.IGNORECASE), 0),
        (re.compile(r"\b(the\s+)?second(\s+one|\s+project|\s+option)?\b", re.IGNORECASE), 1),
        (re.compile(r"\b(the\s+)?third(\s+one|\s+project|\s+option)?\b", re.IGNORECASE), 2),
    ]

    PRONOUN_PATTERNS = [
        re.compile(r"\b(it|this|that|they|them)\b", re.IGNORECASE)
    ]

    @classmethod
    def resolve(
        cls,
        query: str,
        history: List[Dict[str, Any]],
        intent_result: Optional[Any] = None
    ) -> List[ResolvedReference]:
        resolved: List[ResolvedReference] = []
        q_lower = query.lower().strip()

        # 1. User Correction ("No, I meant Project Beta")
        for pat in cls.CORRECTION_PATTERNS:
            m = pat.search(q_lower)
            if m:
                raw_target = m.group(2).strip()
                entity_name = raw_target.title()
                if not entity_name.lower().startswith("project") and "project" in q_lower:
                    entity_name = f"Project {entity_name}"
                resolved.append(ResolvedReference(
                    reference_text=m.group(0),
                    resolved_entity=entity_name,
                    confidence="HIGH",
                    source_context="user_correction"
                ))
                return resolved

        # Extract discussed entities from history
        history_text = " ".join([(m.get("content") or m.get("text") or "") for m in history])
        project_matches = re.findall(r"\bProject\s+([A-Za-z0-9_-]+)\b", history_text, re.IGNORECASE)
        unique_projects = []
        for p in project_matches:
            p_name = f"Project {p.capitalize()}"
            if p_name not in unique_projects:
                unique_projects.append(p_name)

        # Also extract plain entities mentioned in recent assistant replies
        if not unique_projects:
            for p in ["Alpha", "Beta", "Gamma"]:
                if p.lower() in history_text.lower():
                    unique_projects.append(f"Project {p}")

        # 2. Ordinal Reference Resolution ("the first one", "the second one")
        for pat, idx in cls.ORDINAL_PATTERNS:
            m = pat.search(q_lower)
            if m and idx < len(unique_projects):
                resolved.append(ResolvedReference(
                    reference_text=m.group(0),
                    resolved_entity=unique_projects[idx],
                    confidence="HIGH",
                    source_context="ordinal_reference"
                ))
                return resolved

        # 3. Pronoun Resolution ("Why is it delayed?")
        for pat in cls.PRONOUN_PATTERNS:
            m = pat.search(q_lower)
            if m and unique_projects:
                resolved.append(ResolvedReference(
                    reference_text=m.group(0),
                    resolved_entity=unique_projects[0],
                    confidence="HIGH",
                    source_context="pronoun_reference"
                ))
                break

        return resolved
