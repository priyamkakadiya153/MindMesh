from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ToolMetadata(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    permissions: List[str] = Field(default_factory=list)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
