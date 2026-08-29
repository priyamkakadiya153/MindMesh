from pydantic import BaseModel
from typing import Optional

class SectionItem(BaseModel):
    level: str
    title: str
    page: Optional[int] = None
