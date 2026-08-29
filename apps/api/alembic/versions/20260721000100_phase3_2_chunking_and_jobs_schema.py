"""Phase 3.2 Document Text Extraction and Intelligent Chunking schema

Revision ID: 20260721000100
Revises: 20260720000300
Create Date: 2026-07-21 00:01:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '20260721000100'
down_revision: Union[str, None] = '20260720000300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Update document_chunks table
    op.add_column('document_chunks', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.add_column('document_chunks', sa.Column('workspace_id', sa.UUID(), nullable=True))
    op.add_column('document_chunks', sa.Column('page_number', sa.Integer(), nullable=True))
    op.add_column('document_chunks', sa.Column('section_title', sa.String(length=255), nullable=True))
    op.add_column('document_chunks', sa.Column('character_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('document_chunks', sa.Column('checksum', sa.String(length=64), nullable=False, server_default=''))

    op.create_index(op.f('ix_document_chunks_organization_id'), 'document_chunks', ['organization_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_workspace_id'), 'document_chunks', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_chunk_index'), 'document_chunks', ['chunk_index'], unique=False)

    # 2. Create document_processing_jobs table
    op.create_table(
        'document_processing_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='QUEUED'),
        sa.Column('progress', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processing_time_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_processing_jobs_document_id'), 'document_processing_jobs', ['document_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_document_processing_jobs_document_id'), table_name='document_processing_jobs')
    op.drop_table('document_processing_jobs')

    op.drop_index(op.f('ix_document_chunks_chunk_index'), table_name='document_chunks')
    op.drop_index(op.f('ix_document_chunks_workspace_id'), table_name='document_chunks')
    op.drop_index(op.f('ix_document_chunks_organization_id'), table_name='document_chunks')

    op.drop_column('document_chunks', 'checksum')
    op.drop_column('document_chunks', 'character_count')
    op.drop_column('document_chunks', 'section_title')
    op.drop_column('document_chunks', 'page_number')
    op.drop_column('document_chunks', 'workspace_id')
    op.drop_column('document_chunks', 'organization_id')
