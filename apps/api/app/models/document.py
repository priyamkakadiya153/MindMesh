from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, Integer, Text, JSON
from uuid import UUID
from typing import List, Optional
from .base import BaseEntity
try:
    from ..documents.models import Document, DocumentUploadJob, DocumentMetadata, FileIntelligence, DocumentVersion, DocumentAuditLog, RetentionPolicy, Folder, DocumentFavorite, DocumentShare
except ImportError:
    pass
from ..processing.models import DocumentContent
from ..knowledge.models import KnowledgeEntry, ProcessingEvent, DocumentStatistic

from ..ai.embeddings.models import DocumentChunk, DocumentEmbedding
