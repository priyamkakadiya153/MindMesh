import re
import uuid
import time
from typing import List, Dict, Any, Optional, Tuple
from app.ai.knowledge.entity_models import (
    CanonicalEntity,
    EntityType,
    EntityStatus,
    ConfidenceLevel,
    EntityAmbiguity
)

class EntityRegistry:
    """Central Registry storing CanonicalEntities, Aliases, and Identifiers."""

    _instance: Optional["EntityRegistry"] = None

    def __init__(self):
        self._entities: Dict[uuid.UUID, CanonicalEntity] = {}
        self._identifier_map: Dict[str, uuid.UUID] = {}  # "sys:id" -> entity_id
        self._name_map: Dict[str, uuid.UUID] = {}        # "lowercase_name" -> entity_id
        self._alias_map: Dict[str, uuid.UUID] = {}       # "lowercase_alias" -> entity_id

    @classmethod
    def get_instance(cls) -> "EntityRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, entity: CanonicalEntity) -> CanonicalEntity:
        self._entities[entity.entity_id] = entity
        norm_name = entity.canonical_name.lower().strip()
        self._name_map[norm_name] = entity.entity_id

        for alias in entity.aliases:
            self._alias_map[alias.lower().strip()] = entity.entity_id

        for sys, sys_id in entity.identifiers.items():
            self._identifier_map[f"{sys.lower()}:{sys_id.lower()}"] = entity.entity_id

        return entity

    def get_by_id(self, entity_id: uuid.UUID) -> Optional[CanonicalEntity]:
        return self._entities.get(entity_id)

    def lookup_identifier(self, system: str, identifier_val: str) -> Optional[CanonicalEntity]:
        key = f"{system.lower()}:{identifier_val.lower()}"
        eid = self._identifier_map.get(key)
        return self._entities.get(eid) if eid else None

    def search_by_name_or_alias(self, query: str, workspace_id: Optional[uuid.UUID] = None) -> List[CanonicalEntity]:
        norm = query.lower().strip()
        matches = []

        # Check exact name
        if norm in self._name_map:
            matches.append(self._entities[self._name_map[norm]])

        # Check exact alias
        if norm in self._alias_map:
            e = self._entities[self._alias_map[norm]]
            if e not in matches:
                matches.append(e)

        # Check partial/display_name match
        for e in self._entities.values():
            if workspace_id and e.workspace_id and e.workspace_id != workspace_id:
                continue
            if e not in matches:
                c_name = e.canonical_name.lower()
                d_name = e.display_name.lower()
                aliases_lower = [a.lower() for a in e.aliases]
                if (norm == d_name or norm in c_name or norm in d_name or c_name in norm or
                    any(norm in a or a in norm for a in aliases_lower)):
                    matches.append(e)

        return matches


class EntityResolutionEngine:
    """
    Resolves raw text mentions into CanonicalEntities using weighted match signals:
    Exact Identifier > Exact Name > Alias Match > Partial Match.
    Flags EntityAmbiguity when top candidate scores tie.
    """

    @classmethod
    def resolve_mention(
        cls,
        mention: str,
        workspace_id: Optional[uuid.UUID] = None,
        expected_type: Optional[EntityType] = None
    ) -> Tuple[Optional[CanonicalEntity], Optional[EntityAmbiguity]]:
        registry = EntityRegistry.get_instance()
        m_clean = mention.strip()

        # 1. Exact Identifier Match (e.g. "JIRA:PROJ-123")
        id_match = re.match(r"^([a-zA-Z0-9_-]+):([a-zA-Z0-9_-]+)$", m_clean)
        if id_match:
            sys, val = id_match.group(1), id_match.group(2)
            found = registry.lookup_identifier(sys, val)
            if found:
                return found, None

        # 2. Search Name & Aliases in Registry
        candidates = registry.search_by_name_or_alias(m_clean, workspace_id)
        if expected_type:
            candidates = [c for c in candidates if c.entity_type == expected_type]

        if not candidates:
            return None, None

        if len(candidates) == 1:
            return candidates[0], None

        # Check score ties for top candidates
        cand_scores = []
        for c in candidates:
            score = 0.60
            if c.canonical_name.lower() == m_clean.lower():
                score = 0.95
            elif any(a.lower() == m_clean.lower() for a in c.aliases):
                score = 0.85
            cand_scores.append((score, c))

        cand_scores.sort(key=lambda x: x[0], reverse=True)

        # Disambiguation needed if top 2 candidates have equal top score
        if len(cand_scores) > 1 and cand_scores[0][0] == cand_scores[1][0]:
            tied_cands = [c for score, c in cand_scores if score == cand_scores[0][0]]
            names = " or ".join([c.display_name for c in tied_cands])
            ambiguity = EntityAmbiguity(
                mention=m_clean,
                candidates=tied_cands,
                reason="MULTIPLE_MATCHING_CANDIDATES",
                confidence=ConfidenceLevel.UNRESOLVED,
                clarification_prompt=f"Do you mean {names}?"
            )
            return None, ambiguity

        return cand_scores[0][1], None
