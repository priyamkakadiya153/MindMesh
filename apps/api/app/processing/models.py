from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Text, JSON
from uuid import UUID
from ..models.base import BaseEntity

class DocumentContent(BaseEntity):
    __tablename__ = "document_contents"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False, unique=True)
    content_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    statistics: Mapped[dict] = mapped_column(JSON, nullable=False)

    document: Mapped["Document"] = relationship()
