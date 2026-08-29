"""embedding tables

Revision ID: 20260705000400
Revises: 20260705000300
Create Date: 2026-07-05 00:04:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260705000400'
down_revision: Union[str, None] = '20260705000300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Check if document_chunks table already exists (if it was created by legacy schemas)
    # We drop and recreate it to match the clean schema
    op.execute("DROP TABLE IF EXISTS document_chunks CASCADE")

    op.create_table(
        'document_chunks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE')
    )
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])

    op.create_table(
        'document_embeddings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('chunk_id', sa.UUID(), nullable=False),
        sa.Column('embedding_model', sa.String(100), nullable=False),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False),
        sa.Column('vector_id', sa.UUID(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=False),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['chunk_id'], ['document_chunks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vector_id'], ['document_chunks.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('chunk_id')
    )
    op.create_index('ix_document_embeddings_chunk_id', 'document_embeddings', ['chunk_id'])

def downgrade() -> None:
    op.drop_index('ix_document_embeddings_chunk_id', 'document_embeddings')
    op.drop_table('document_embeddings')
    op.drop_index('ix_document_chunks_document_id', 'document_chunks')
    op.drop_table('document_chunks')
