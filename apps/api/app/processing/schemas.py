from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID

class SectionSchema(BaseModel):
    level: str
    title: str
    page: Optional[int] = None

class ParagraphSchema(BaseModel):
    text: str

class TableSchema(BaseModel):
    table_index: Optional[int] = None
    sheet_name: Optional[str] = None
    data: List[List[Any]]

class ImageSchema(BaseModel):
    image_index: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    src: Optional[str] = None
    alt: Optional[str] = None

class NormalizedContentModel(BaseModel):
    title: str
    metadata: Dict[str, Any]
    sections: List[SectionSchema]
    paragraphs: List[ParagraphSchema]
    tables: List[TableSchema]
    images: List[ImageSchema]
    links: List[Dict[str, Any]]
    language: str
    statistics: Dict[str, Any]

class ProcessResponse(BaseModel):
    document_id: UUID
    status: str
    message: str

class StatisticsResponse(BaseModel):
    document_id: UUID
    word_count: int
    character_count: int
    page_count: int
    table_count: int
    image_count: int
