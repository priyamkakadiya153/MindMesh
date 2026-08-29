import logging
import json
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.cognitive_agent import CognitiveAgent, CognitiveAgentExecution, CognitiveAgentOutput, CognitiveAgentMemory
from app.models.user import User

logger = logging.getLogger(__name__)

TRIVIAL_PHRASES = [
    "hello", "hi", "thanks", "thank you", "okay", "ok", "got it", "2 + 2 = 4"
]

class CognitiveAgentMemoryService:
    """
    CA-09 — Cognitive Agent Durable Memory & Context Management Service.
    Manages durable, provenance-backed memory records with status lifecycle (ACTIVE, SUPERSEDED, EXPIRED, CONFLICT).

    CRITICAL PRINCIPLE:
    MEMORY NEVER GRANTS PERMISSION.
    A memory record is context, NOT authorization.
    Every retrieval must still revalidate current user permissions and CA-04 scope.
    """

    @staticmethod
    async def create_memory(
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID,
        workspace_id: Optional[UUID],
        created_by_user_id: UUID,
        memory_type: str,
        key: str,
        content: str,
        confidence: float = 0.9,
        confidence_level: str = "CONFIRMED",
        source_execution_id: Optional[UUID] = None,
        source_output_id: Optional[UUID] = None,
        source_entity_type: Optional[str] = None,
        source_entity_id: Optional[str] = None
    ) -> CognitiveAgentMemory:
        """
        Creates a new CognitiveAgentMemory record.
        If an active memory with the same key already exists, supersedes the old memory entry.
        """
        # Check existing active memory for key
        stmt = select(CognitiveAgentMemory).where(
            CognitiveAgentMemory.agent_id == agent_id,
            CognitiveAgentMemory.organization_id == organization_id,
            CognitiveAgentMemory.key == key,
            CognitiveAgentMemory.status == "ACTIVE"
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        new_mem = CognitiveAgentMemory(
            agent_id=agent_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            created_by_user_id=created_by_user_id,
            memory_type=memory_type.upper(),
            status="ACTIVE",
            key=key,
            content=content,
            confidence=confidence,
            confidence_level=confidence_level.upper(),
            source_execution_id=source_execution_id,
            source_output_id=source_output_id,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id
        )
        db.add(new_mem)
        await db.flush()

        if existing:
            existing.status = "SUPERSEDED"
            existing.superseded_by_id = new_mem.id
            existing.updated_at = datetime.now(timezone.utc)
            logger.info(f"[CognitiveMemory] Memory {existing.id} superseded by new memory {new_mem.id} for key '{key}'.")

        await db.commit()
        await db.refresh(new_mem)
        return new_mem

    @staticmethod
    async def list_agent_memories(
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        memory_type: Optional[str] = None
    ) -> List[CognitiveAgentMemory]:
        """
        Retrieves active durable memories for an agent.
        Enforces organization and workspace isolation boundaries.
        """
        stmt = select(CognitiveAgentMemory).where(
            CognitiveAgentMemory.agent_id == agent_id,
            CognitiveAgentMemory.organization_id == organization_id,
            CognitiveAgentMemory.status == "ACTIVE",
            CognitiveAgentMemory.is_active == True
        )
        if workspace_id:
            stmt = stmt.where(CognitiveAgentMemory.workspace_id == workspace_id)
        if memory_type:
            stmt = stmt.where(CognitiveAgentMemory.memory_type == memory_type.upper())

        stmt = stmt.order_by(CognitiveAgentMemory.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def delete_memory(
        db: AsyncSession,
        agent_id: UUID,
        memory_id: UUID,
        organization_id: UUID
    ) -> bool:
        """
        Soft-deletes a specific memory record.
        """
        stmt = select(CognitiveAgentMemory).where(
            CognitiveAgentMemory.id == memory_id,
            CognitiveAgentMemory.agent_id == agent_id,
            CognitiveAgentMemory.organization_id == organization_id
        )
        res = await db.execute(stmt)
        mem = res.scalar_one_or_none()
        if not mem:
            return False

        mem.is_active = False
        mem.status = "EXPIRED"
        mem.expired_at = datetime.now(timezone.utc)
        await db.commit()
        return True

    @staticmethod
    async def extract_and_persist_memories(
        db: AsyncSession,
        agent: CognitiveAgent,
        execution: CognitiveAgentExecution,
        output: CognitiveAgentOutput,
        current_user: User,
        organization_id: UUID,
        workspace_id: UUID
    ) -> List[CognitiveAgentMemory]:
        """
        Conservatively extracts durable memories from agent execution output.
        Suppresses trivial conversation ("Hello", "Okay", "2+2=4").
        """
        if not output or not output.body:
            return []

        body_text = output.body.strip()
        body_lower = body_text.lower()

        # Reject trivial text
        for trivial in TRIVIAL_PHRASES:
            if body_lower == trivial or body_lower.startswith(trivial + "."):
                logger.info(f"[CognitiveMemory] Trivial response '{body_text}' rejected for durable memory creation.")
                return []

        created_memories: List[CognitiveAgentMemory] = []

        # Grounded Provenance Reference
        source_entity_type = None
        source_entity_id = None
        if output.provenance and len(output.provenance) > 0:
            first_prov = output.provenance[0]
            source_entity_type = first_prov.get("source_type")
            source_entity_id = first_prov.get("source_id") or first_prov.get("conversation_id")

        # 1. Epistemic / Topic memory
        memory_key = f"context:{agent.name}:{output.title[:50]}"
        mem = await CognitiveAgentMemoryService.create_memory(
            db=db,
            agent_id=agent.id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            created_by_user_id=current_user.id,
            memory_type="EPISODIC",
            key=memory_key,
            content=f"Agent observed: {output.title} — {body_text[:250]}",
            confidence=0.9,
            confidence_level="OBSERVED",
            source_execution_id=execution.id,
            source_output_id=output.id,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id
        )
        created_memories.append(mem)

        return created_memories
