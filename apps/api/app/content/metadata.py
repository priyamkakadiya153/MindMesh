from pydantic import BaseModel
from typing import Optional, Dict, Any

class MetadataItem(BaseModel):
    properties: Dict[str, Any]
