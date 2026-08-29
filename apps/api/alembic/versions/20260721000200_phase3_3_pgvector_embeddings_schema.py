"""Phase 3.3 Enterprise Embedding Generation with pgvector schema

Revision ID: 20260721000200
Revises: 20260721000100
Create Date: 2026-07-21 00:02:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260721000200'
down_revision: Union[str, None] = '20260721000100'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Enable pgvector extension if available
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Add relational columns to document_embeddings table
    op.add_column('document_embeddings', sa.Column('document_id', sa.UUID(), nullable=True))
    op.add_column('document_embeddings', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.add_column('document_embeddings', sa.Column('workspace_id', sa.UUID(), nullable=True))
    op.add_column('document_embeddings', sa.Column('embedding_version', sa.Integer(), nullable=False, server_default='1'))

    op.create_index(op.f('ix_document_embeddings_document_id'), 'document_embeddings', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_embeddings_organization_id'), 'document_embeddings', ['organization_id'], unique=False)
    op.create_index(op.f('ix_document_embeddings_workspace_id'), 'document_embeddings', ['workspace_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_document_embeddings_workspace_id'), table_name='document_embeddings')
    op.drop_index(op.f('ix_document_embeddings_organization_id'), table_name='document_embeddings')
    op.drop_index(op.f('ix_document_embeddings_document_id'), table_name='document_embeddings')

    op.drop_column('document_embeddings', 'embedding_version')
    op.drop_column('document_embeddings', 'workspace_id')
    op.drop_column('document_embeddings', 'organization_id')
    op.drop_column('document_embeddings', 'document_id')
