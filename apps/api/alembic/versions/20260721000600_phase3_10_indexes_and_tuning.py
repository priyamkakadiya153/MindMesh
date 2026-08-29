"""Phase 3.10 Performance Indexes & HNSW Vector Tuning

Revision ID: 20260721000600
Revises: 20260721000500
Create Date: 2026-07-21 00:06:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260721000600'
down_revision: Union[str, None] = '20260721000500'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. HNSW Index for pgvector
    op.execute("CREATE INDEX IF NOT EXISTS ix_document_embeddings_hnsw ON document_embeddings USING hnsw (embedding vector_cosine_ops);")

    # 2. Performance B-Tree Indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_document_chunks_doc_id ON document_chunks (document_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_document_chunks_org_ws ON document_chunks (organization_id, workspace_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_document_embeddings_org_ws ON document_embeddings (organization_id, workspace_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_messages_chat_created ON messages (chat_id, created_at);")

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_messages_chat_created;")
    op.execute("DROP INDEX IF EXISTS ix_document_embeddings_org_ws;")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_org_ws;")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_doc_id;")
    op.execute("DROP INDEX IF EXISTS ix_document_embeddings_hnsw;")
