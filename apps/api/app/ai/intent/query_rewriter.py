import re
from typing import List, Dict, Any, Optional, Tuple

class QueryRewriter:
    """
    Contextual Query Rewriter for MindMesh Follow-Up Queries.
    Resolves conversational entity references ('the first one', 'it') into explicit contextual queries.
    """

    @classmethod
    def rewrite(
        cls,
        query: str,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        if not history:
            return None, None

        q_lower = query.lower().strip()

        # Find recent assistant message content
        recent_text = ""
        for msg in reversed(history):
            content = msg.get("content") or msg.get("text") or ""
            if content:
                recent_text += " " + content

        # Extract entities mentioned in history (e.g., Project Alpha, Project Beta)
        project_matches = re.findall(r"\bProject\s+([A-Za-z0-9_-]+)\b", recent_text, re.IGNORECASE)
        unique_projects = []
        for p in project_matches:
            full_name = f"Project {p.capitalize()}"
            if full_name not in unique_projects:
                unique_projects.append(full_name)

        target_ref = None

        if "first" in q_lower or "the first one" in q_lower:
            if unique_projects:
                target_ref = unique_projects[0]
        elif "second" in q_lower or "the second one" in q_lower:
            if len(unique_projects) > 1:
                target_ref = unique_projects[1]
        elif any(w in q_lower for w in ["it", "this", "that"]) and unique_projects:
            target_ref = unique_projects[0]

        if target_ref:
            rewritten = f"What is the status and details of {target_ref}?"
            return rewritten, target_ref

        return None, None
