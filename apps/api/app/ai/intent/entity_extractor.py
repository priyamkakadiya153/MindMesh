import re
from typing import List, Tuple, Optional, Dict, Any
from app.ai.intent.models import EntityMention, EntitySource, ConfidenceLevel

class EntityExtractor:
    """
    Extracts entity mentions and contextual references from query strings.
    """

    KNOWN_TECHS = {"python", "fastapi", "react", "typescript", "javascript", "postgresql", "sqlite", "docker", "kubernetes", "http", "rest", "graphql"}
    PRONOUN_PATTERNS = [
        re.compile(r"\b(the first one|the second one|the previous one|the former|the latter|it|this|that|those|these)\b", re.IGNORECASE)
    ]
    PROJECT_PATTERNS = [
        re.compile(r"\bproject\s+([A-Z0-9a-z_-]+)\b", re.IGNORECASE),
        re.compile(r"\b([A-Z0-9a-z_-]+)\s+project\b", re.IGNORECASE),
    ]
    DOC_PATTERNS = [
        re.compile(r"\b([A-Z0-9a-z_.-]+\.(pdf|md|doc|docx|txt|json))\b", re.IGNORECASE),
        re.compile(r"\b(architecture|security|api|financial|release)\s+(pdf|document|file|report|spec)\b", re.IGNORECASE)
    ]

    @classmethod
    def extract(
        cls,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[List[EntityMention], List[str]]:
        entities: List[EntityMention] = []
        references: List[str] = []
        q_lower = query.lower()

        # 1. Extract Tech Entities
        words = re.findall(r"\b[a-zA-Z0-9_-]+\b", q_lower)
        for w in words:
            if w in cls.KNOWN_TECHS:
                entities.append(EntityMention(
                    text=w,
                    type="Technology",
                    source=EntitySource.EXPLICIT,
                    confidence=ConfidenceLevel.HIGH
                ))

        # 2. Extract Project Entities
        for pat in cls.PROJECT_PATTERNS:
            for m in pat.finditer(query):
                pname = m.group(1)
                if pname.lower() not in {"this", "that", "the", "a", "our", "my"}:
                    entities.append(EntityMention(
                        text=f"Project {pname.capitalize()}",
                        type="Project",
                        source=EntitySource.EXPLICIT,
                        confidence=ConfidenceLevel.HIGH
                    ))

        # 3. Extract Document Entities
        for pat in cls.DOC_PATTERNS:
            for m in pat.finditer(query):
                doc_name = m.group(0)
                entities.append(EntityMention(
                    text=doc_name,
                    type="Document",
                    source=EntitySource.EXPLICIT,
                    confidence=ConfidenceLevel.HIGH
                ))

        # 4. Extract Pronoun References
        for pat in cls.PRONOUN_PATTERNS:
            for m in pat.finditer(query):
                references.append(m.group(0))

        return entities, references
