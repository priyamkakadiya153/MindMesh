from pydantic import BaseModel

class HyperlinkItem(BaseModel):
    url: str
    text: str
