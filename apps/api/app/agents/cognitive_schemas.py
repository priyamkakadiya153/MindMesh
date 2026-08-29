"""
MindMesh — Cognitive Agent Pydantic Request / Response Schemas (CA-02)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.agents.cognitive_contracts import (
    CognitiveAgentStatus,
    CognitiveAgentType,
    CognitiveAgentScopeContract,
    CognitiveAgentTriggerContract,
    CognitiveAgentOutputType,
    CognitiveAgentExecutionStatus
)


class CognitiveAgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    agent_type: CognitiveAgentType = CognitiveAgentType.CUSTOM
    instructions: str = Field(..., min_length=1, max_length=10000)
    workspace_id: Optional[UUID] = None
    enabled: bool = True
    knowledge_scope: Optional[CognitiveAgentScopeContract] = None
    triggers: Optional[List[CognitiveAgentTriggerContract]] = None


class CognitiveAgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    instructions: Optional[str] = Field(None, min_length=1, max_length=10000)
    status: Optional[CognitiveAgentStatus] = None
    enabled: Optional[bool] = None
    knowledge_scope: Optional[CognitiveAgentScopeContract] = None
    triggers: Optional[List[CognitiveAgentTriggerContract]] = None


class CognitiveAgentResponse(BaseModel):
    id: UUID
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    owner_user_id: UUID
    name: str
    description: Optional[str] = None
    agent_type: str
    instructions: str
    status: str
    enabled: bool
    knowledge_scope: Optional[Dict[str, Any]] = None
    triggers: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CognitiveAgentExecutionCreate(BaseModel):
    trigger_type: str = "MANUAL"
    input_context: Optional[Dict[str, Any]] = None


class CognitiveAgentExecutionResponse(BaseModel):
    id: UUID
    agent_id: UUID
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    triggered_by: Optional[UUID] = None
    trigger_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    input_context: Optional[Dict[str, Any]] = None
    output_summary: Optional[str] = None
    action_candidates_generated: int = 0
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CognitiveAgentOutputCreate(BaseModel):
    output_type: CognitiveAgentOutputType = CognitiveAgentOutputType.INSIGHT
    title: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., min_length=1)
    candidate_type: Optional[str] = None
    structured_payload: Optional[Dict[str, Any]] = None
    provenance: Optional[List[Dict[str, Any]]] = None


class CognitiveAgentOutputResponse(BaseModel):
    id: UUID
    execution_id: UUID
    agent_id: UUID
    organization_id: UUID
    workspace_id: Optional[UUID] = None
    output_type: str
    title: str
    body: str
    candidate_type: Optional[str] = None
    structured_payload: Optional[Dict[str, Any]] = None
    provenance: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True
