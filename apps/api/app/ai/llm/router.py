import logging
from uuid import UUID
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from .base import LLMSettings
from .factory import LLMProviderFactory
from .registry import LLMModelRegistry
from .models import WorkspaceAISetting

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["Multi-LLM Provider Platform"])

# ---------------- PYDANTIC SCHEMAS ----------------

class AISettingsResponse(BaseModel):
    workspace_id: UUID
    organization_id: UUID
    provider: str
    model: str
    temperature: float
    top_p: float
    max_tokens: int
    fallback_provider: str
    fallback_model: str
    system_prompt: Optional[str] = None

class UpdateAISettingsRequest(BaseModel):
    workspace_id: UUID
    provider: Optional[str] = Field(None, description="gemini, openai, claude, ollama")
    model: Optional[str] = Field(None, description="Model ID")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, ge=256, le=16384)
    fallback_provider: Optional[str] = Field(None)
    fallback_model: Optional[str] = Field(None)
    system_prompt: Optional[str] = Field(None)

class TestLLMRequest(BaseModel):
    prompt: str = Field("Explain MindMesh in one sentence.", min_length=1)
    workspace_id: Optional[UUID] = None
    provider: Optional[str] = None
    model: Optional[str] = None

class TestLLMResponse(BaseModel):
    content: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    latency_ms: int
    finish_reason: str

# ---------------- ENDPOINTS ----------------

@router.get("/providers", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_providers_endpoint():
    """Lists available cloud & local LLM providers."""
    return [
        {"id": "gemini", "name": "Google Gemini", "type": "cloud", "status": "active"},
        {"id": "openai", "name": "OpenAI", "type": "cloud", "status": "active"},
        {"id": "claude", "name": "Anthropic Claude", "type": "cloud", "status": "active"},
        {"id": "ollama", "name": "Ollama (Local)", "type": "local", "status": "active"},
        {"id": "mock", "name": "Mock Fallback", "type": "mock", "status": "active"}
    ]

@router.get("/models", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def get_models_endpoint():
    """Lists all registered LLM models with token pricing metadata."""
    return LLMModelRegistry.list_all_models()

@router.get("/settings", response_model=AISettingsResponse, status_code=status.HTTP_200_OK)
async def get_workspace_ai_settings_endpoint(
    workspace_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetches workspace AI configuration settings."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    stmt = select(WorkspaceAISetting).where(WorkspaceAISetting.workspace_id == workspace_id)
    setting = (await db.execute(stmt)).scalar_one_or_none()

    if not setting:
        # Create default workspace setting if missing
        setting = WorkspaceAISetting(
            workspace_id=workspace_id,
            organization_id=org_uuid,
            provider="gemini",
            model="gemini-2.5-flash",
            temperature=0.7,
            top_p=0.95,
            max_tokens=2048,
            fallback_provider="openai",
            fallback_model="gpt-4o-mini"
        )
        db.add(setting)
        await db.commit()
        await db.refresh(setting)

    return AISettingsResponse(
        workspace_id=setting.workspace_id,
        organization_id=setting.organization_id,
        provider=setting.provider,
        model=setting.model,
        temperature=setting.temperature,
        top_p=setting.top_p,
        max_tokens=setting.max_tokens,
        fallback_provider=setting.fallback_provider,
        fallback_model=setting.fallback_model,
        system_prompt=setting.system_prompt
    )

@router.patch("/settings", response_model=AISettingsResponse, status_code=status.HTTP_200_OK)
async def update_workspace_ai_settings_endpoint(
    request: UpdateAISettingsRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Updates workspace AI provider & generation configuration."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    stmt = select(WorkspaceAISetting).where(WorkspaceAISetting.workspace_id == request.workspace_id)
    setting = (await db.execute(stmt)).scalar_one_or_none()

    if not setting:
        setting = WorkspaceAISetting(workspace_id=request.workspace_id, organization_id=org_uuid)
        db.add(setting)

    if request.provider is not None:
        setting.provider = request.provider
    if request.model is not None:
        setting.model = request.model
    if request.temperature is not None:
        setting.temperature = request.temperature
    if request.top_p is not None:
        setting.top_p = request.top_p
    if request.max_tokens is not None:
        setting.max_tokens = request.max_tokens
    if request.fallback_provider is not None:
        setting.fallback_provider = request.fallback_provider
    if request.fallback_model is not None:
        setting.fallback_model = request.fallback_model
    if request.system_prompt is not None:
        setting.system_prompt = request.system_prompt

    await db.commit()
    await db.refresh(setting)

    return AISettingsResponse(
        workspace_id=setting.workspace_id,
        organization_id=setting.organization_id,
        provider=setting.provider,
        model=setting.model,
        temperature=setting.temperature,
        top_p=setting.top_p,
        max_tokens=setting.max_tokens,
        fallback_provider=setting.fallback_provider,
        fallback_model=setting.fallback_model,
        system_prompt=setting.system_prompt
    )

@router.get("/health", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def health_check_all_providers():
    """Performs health check and latency diagnostic on all AI providers."""
    providers = ["gemini", "openai", "claude", "ollama"]
    health_results = []
    for p_name in providers:
        adapter = LLMProviderFactory.get_provider(p_name)
        res = await adapter.health_check()
        health_results.append(res)
    return health_results

@router.post("/test", response_model=TestLLMResponse, status_code=status.HTTP_200_OK)
async def test_llm_connection_endpoint(
    request: TestLLMRequest,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes a test LLM generation using the workspace settings or specified provider."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    cfg = LLMSettings()
    if request.workspace_id:
        stmt = select(WorkspaceAISetting).where(WorkspaceAISetting.workspace_id == request.workspace_id)
        setting = (await db.execute(stmt)).scalar_one_or_none()
        if setting:
            cfg.provider = setting.provider
            cfg.model = setting.model
            cfg.temperature = setting.temperature
            cfg.top_p = setting.top_p
            cfg.max_tokens = setting.max_tokens
            cfg.fallback_provider = setting.fallback_provider
            cfg.fallback_model = setting.fallback_model

    if request.provider:
        cfg.provider = request.provider
    if request.model:
        cfg.model = request.model

    res = await LLMProviderFactory.generate_with_failover(
        prompt=request.prompt,
        system_prompt=cfg.system_prompt or "You are MindMesh AI testing your multi-provider integration.",
        settings=cfg
    )

    return TestLLMResponse(
        content=res.content,
        model=res.model,
        provider=res.provider,
        prompt_tokens=res.prompt_tokens,
        completion_tokens=res.completion_tokens,
        total_tokens=res.total_tokens,
        estimated_cost_usd=res.estimated_cost_usd,
        latency_ms=res.latency_ms,
        finish_reason=res.finish_reason
    )
