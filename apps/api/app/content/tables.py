from pydantic import BaseModel
from typing import List, Any, Optional

class TableItem(BaseModel):
    table_index: Optional[int] = None
    sheet_name: Optional[str] = None
    data: List[List[Any]]
