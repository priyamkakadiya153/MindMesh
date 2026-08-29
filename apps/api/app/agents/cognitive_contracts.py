"""
MindMesh — Cognitive Agent Domain Contracts & Foundation Interfaces (CA-01)

Establishes formal Pydantic data structures, domain enums, scope definitions,
and integration functions mapping Cognitive Agent outputs to the MindMesh Action Candidate system.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

from app.actions.candidate import (
    ActionCandidate,
    ProvenanceContext,
    IntentCategory,
    ActionType,
    UserResponsibilityRole,
    ConfidenceLevel,
    CandidateStatus
)


class CognitiveAgentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"
    ARCHIVED = "ARCHIVED"


class CognitiveAgentType(str, Enum):
    KNOWLEDGE_SYNTHESIZER = "KNOWLEDGE_SYNTHESIZER"
    DISCUSSION_ANALYZER = "DISCUSSION_ANALYZER"
    DOCUMENT_PARSER = "DOCUMENT_PARSER"
    PROJECT_MONITOR = "PROJECT_MONITOR"
    CUSTOM = "CUSTOM"


class CognitiveAgentScopeType(str, Enum):
    WORKSPACE = "WORKSPACE"
    PROJECT = "PROJECT"
    DOCUMENT = "DOCUMENT"
    CONVERSATION = "CONVERSATION"
    CHANNEL = "CHANNEL"
    SELECTED_KNOWLEDGE = "SELECTED_KNOWLEDGE"


class CognitiveAgentTriggerType(str, Enum):
    MANUAL = "MANUAL"
    CONVERSATION_EVENT = "CONVERSATION_EVENT"
    DOCUMENT_EVENT = "DOCUMENT_EVENT"
    PROJECT_EVENT = "PROJECT_EVENT"
    SCHEDULE = "SCHEDULE"


class CognitiveAgentOutputType(str, Enum):
    INSIGHT = "INSIGHT"
    SUMMARY = "SUMMARY"
    RECOMMENDATION = "RECOMMENDATION"
    ACTION_CANDIDATE = "ACTION_CANDIDATE"


class CognitiveAgentExecutionStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class CognitiveAgentScopeContract(BaseModel):
    scope_type: CognitiveAgentScopeType = CognitiveAgentScopeType.WORKSPACE
    workspace_id: Optional[str] = None
    project_id: Optional[str] = None
    document_ids: List[str] = Field(default_factory=list)
    conversation_ids: List[str] = Field(default_factory=list)
    channel_ids: List[str] = Field(default_factory=list)
    restricted_knowledge_keys: List[str] = Field(default_factory=list)


class CognitiveAgentTriggerContract(BaseModel):
    trigger_type: CognitiveAgentTriggerType = CognitiveAgentTriggerType.MANUAL
    event_pattern: Optional[str] = None
    cron_expression: Optional[str] = None
    enabled: bool = True


class CognitiveAgentContract(BaseModel):
    """
    Authoritative domain contract for Cognitive Agents in MindMesh.
    """
    id: Optional[str] = None
    organization_id: str
    workspace_id: Optional[str] = None
    owner_user_id: str
    name: str
    description: str = ""
    agent_type: CognitiveAgentType = CognitiveAgentType.CUSTOM
    instructions: str
    status: CognitiveAgentStatus = CognitiveAgentStatus.ACTIVE
    enabled: bool = True
    knowledge_scope: CognitiveAgentScopeContract = Field(default_factory=CognitiveAgentScopeContract)
    triggers: List[CognitiveAgentTriggerContract] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CognitiveAgentProvenanceContract(BaseModel):
    source_type: str = Field(default="CONVERSATION", description="CONVERSATION, DOCUMENT, PROJECT, TASK, DECISION")
    source_id: str
    source_reference: Optional[str] = None
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)


class CognitiveAgentOutputContract(BaseModel):
    """
    Contract for structured agent outputs.
    """
    output_id: Optional[str] = None
    agent_id: str
    organization_id: str
    workspace_id: Optional[str] = None
    output_type: CognitiveAgentOutputType
    title: str
    body: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance: List[CognitiveAgentProvenanceContract] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Action Candidate Specific Fields (when output_type == ACTION_CANDIDATE)
    candidate_type: Optional[str] = "CREATE_TASK"  # CREATE_TASK, CREATE_REMINDER, FOLLOW_UP, REVIEW
    action_type: ActionType = ActionType.TASK
    intent: IntentCategory = IntentCategory.TASK_REQUEST
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = None
    deadline: Optional[str] = None

    def to_action_candidate(self) -> ActionCandidate:
        """
        Converts an ACTION_CANDIDATE agent output into a MindMesh ActionCandidate.
        Enforces AUTO-06 confirmation requirement and complete provenance.
        """
        if self.output_type != CognitiveAgentOutputType.ACTION_CANDIDATE:
            raise ValueError(f"Cannot convert output type '{self.output_type}' to ActionCandidate")

        first_provenance = self.provenance[0] if self.provenance else CognitiveAgentProvenanceContract(
            source_type="COGNITIVE_AGENT",
            source_id=self.agent_id
        )

        provenance_ctx = ProvenanceContext(
            source_type=first_provenance.source_type,
            conversation_id=first_provenance.source_id,
            workspace_id=self.workspace_id
        )

        return ActionCandidate(
            source=provenance_ctx,
            intent=self.intent,
            action_type=self.action_type,
            candidate_type=self.candidate_type or "CREATE_TASK",
            user_role=UserResponsibilityRole.ASSIGNEE,
            subject=self.title,
            description=self.body,
            deadline=self.deadline,
            assignee_id=self.assignee_id,
            assignee_name=self.assignee_name,
            confidence=first_provenance.confidence_score,
            confidence_level=ConfidenceLevel.HIGH if first_provenance.confidence_score >= 0.8 else ConfidenceLevel.MEDIUM,
            requires_user_confirmation=True,  # MANDATORY AUTO-06 SAFETY REQUIREMENT
            status=CandidateStatus.DETECTED,
            provenance={
                "agent_id": self.agent_id,
                "output_id": self.output_id,
                "all_sources": [p.model_dump() for p in self.provenance]
            }
        )


class CognitiveAgentExecutionContract(BaseModel):
    """
    Execution traceability record contract for Cognitive Agent runs.
    """
    execution_id: str
    agent_id: str
    organization_id: str
    workspace_id: Optional[str] = None
    trigger_source: CognitiveAgentTriggerType = CognitiveAgentTriggerType.MANUAL
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    input_context: Dict[str, Any] = Field(default_factory=dict)
    outputs: List[CognitiveAgentOutputContract] = Field(default_factory=list)
    action_candidates_generated: int = 0
    status: CognitiveAgentExecutionStatus = CognitiveAgentExecutionStatus.QUEUED
    error_message: Optional[str] = None
