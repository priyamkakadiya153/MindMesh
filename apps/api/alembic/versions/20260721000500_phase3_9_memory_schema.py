"""Phase 3.9 Conversation Memory & AI Summarization schema

Revision ID: 20260721000500
Revises: 20260721000400
Create Date: 2026-07-21 00:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260721000500'
down_revision: Union[str, None] = '20260721000400'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'conversation_summaries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('message_range_start', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('message_range_end', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('key_decisions', sa.JSON(), nullable=True),
        sa.Column('action_items', sa.JSON(), nullable=True),
        sa.Column('topics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['conversation_id'], ['chats.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_summaries_conversation_id'), 'conversation_summaries', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_conversation_summaries_workspace_id'), 'conversation_summaries', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_conversation_summaries_organization_id'), 'conversation_summaries', ['organization_id'], unique=False)

    op.create_table(
        'conversation_memories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('memory_type', sa.String(length=50), nullable=False, server_default='fact'),
        sa.Column('importance', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expiration_status', sa.String(length=20), nullable=False, server_default='permanent'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['conversation_id'], ['chats.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_memories_conversation_id'), 'conversation_memories', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_conversation_memories_workspace_id'), 'conversation_memories', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_conversation_memories_organization_id'), 'conversation_memories', ['organization_id'], unique=False)

def downgrade() -> None:
    op.drop_table('conversation_memories')
    op.drop_table('conversation_summaries')
