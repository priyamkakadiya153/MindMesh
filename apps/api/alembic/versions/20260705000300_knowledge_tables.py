"""knowledge tables

Revision ID: 20260705000300
Revises: 20260705000200
Create Date: 2026-07-05 00:03:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260705000300'
down_revision: Union[str, None] = '20260705000200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'knowledge_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=False),
        sa.Column('normalized_content', sa.JSON(), nullable=False),
        sa.Column('language', sa.String(50), nullable=False, server_default='en'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('topics', sa.JSON(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('processing_state', sa.String(50), nullable=False, server_default='UPLOADED'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('document_id')
    )
    op.create_index('ix_knowledge_entries_document_id', 'knowledge_entries', ['document_id'])

    op.create_table(
        'processing_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('stage', sa.String(50), nullable=False),
        sa.Column('worker', sa.String(100), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE')
    )
    op.create_index('ix_processing_events_document_id', 'processing_events', ['document_id'])

    op.create_table(
        'document_statistics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('pages', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('words', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('characters', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('paragraphs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tables', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('images', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('headings', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reading_time', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('document_id')
    )
    op.create_index('ix_document_statistics_document_id', 'document_statistics', ['document_id'])

def downgrade() -> None:
    op.drop_index('ix_document_statistics_document_id', 'document_statistics')
    op.drop_table('document_statistics')
    op.drop_index('ix_processing_events_document_id', 'processing_events')
    op.drop_table('processing_events')
    op.drop_index('ix_knowledge_entries_document_id', 'knowledge_entries')
    op.drop_table('knowledge_entries')
