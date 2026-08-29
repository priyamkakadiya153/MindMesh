"""Phase 3.8 Citation Rendering & Source Attribution schema

Revision ID: 20260721000400
Revises: 20260721000300
Create Date: 2026-07-21 00:04:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260721000400'
down_revision: Union[str, None] = '20260721000300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'citations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('chunk_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section_title', sa.String(length=255), nullable=True),
        sa.Column('similarity_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('confidence_score', sa.String(length=20), nullable=False, server_default='High'),
        sa.Column('citation_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('citation_tag', sa.String(length=10), nullable=False, server_default='[1]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['chats.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chunk_id'], ['document_chunks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_citations_message_id'), 'citations', ['message_id'], unique=False)
    op.create_index(op.f('ix_citations_conversation_id'), 'citations', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_citations_document_id'), 'citations', ['document_id'], unique=False)
    op.create_index(op.f('ix_citations_chunk_id'), 'citations', ['chunk_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_citations_chunk_id'), table_name='citations')
    op.drop_index(op.f('ix_citations_document_id'), table_name='citations')
    op.drop_index(op.f('ix_citations_conversation_id'), table_name='citations')
    op.drop_index(op.f('ix_citations_message_id'), table_name='citations')
    op.drop_table('citations')
