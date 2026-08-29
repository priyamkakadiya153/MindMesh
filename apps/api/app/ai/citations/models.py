from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field

class Citation(BaseModel):
    document: str = Field(..., description="Document filename.")
    document_id: UUID = Field(..., description="UUID of the cited document.")
    version: int = Field(default=1, description="Version of the cited document.")
    workspace: str = Field(default="General", description="Workspace name.")
    project: str = Field(default="General", description="Project name.")
    page: Optional[int] = Field(None, description="Page number.")
    section: Optional[str] = Field(None, description="Section heading.")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Similarity matching confidence.")
