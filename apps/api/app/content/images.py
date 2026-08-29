from pydantic import BaseModel
from typing import Optional

class ImageItem(BaseModel):
    image_index: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    src: Optional[str] = None
    alt: Optional[str] = None
