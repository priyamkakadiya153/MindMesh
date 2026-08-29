"""Phase 3 RAG & Chat schema update

Revision ID: 20260720000200
Revises: 20260720000100
Create Date: 2026-07-20 00:02:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260720000200'
down_revision: Union[str, None] = '20260720000100'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add columns to chats table if not exists
    op.add_column('chats', sa.Column('user_id', sa.UUID(), nullable=True))
    op.add_column('chats', sa.Column('workspace_id', sa.UUID(), nullable=True))
    op.add_column('chats', sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('chats', sa.Column('settings', sa.JSON(), nullable=True))
    
    op.create_index(op.f('ix_chats_user_id'), 'chats', ['user_id'], unique=False)
    op.create_index(op.f('ix_chats_workspace_id'), 'chats', ['workspace_id'], unique=False)
    op.create_foreign_key('fk_chats_user_id', 'chats', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_chats_workspace_id', 'chats', 'workspaces', ['workspace_id'], ['id'], ondelete='CASCADE')

    # Add columns to messages table if not exists
    op.add_column('messages', sa.Column('role', sa.String(length=20), nullable=False, server_default='user'))
    op.add_column('messages', sa.Column('model', sa.String(length=100), nullable=True))
    op.add_column('messages', sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('messages', sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'))

    # Create citations table
    op.create_table(
        'citations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('chunk_id', sa.UUID(), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['chunk_id'], ['document_chunks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_citations_document_id'), 'citations', ['document_id'], unique=False)
    op.create_index(op.f('ix_citations_message_id'), 'citations', ['message_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_citations_message_id'), table_name='citations')
    op.drop_index(op.f('ix_citations_document_id'), table_name='citations')
    op.drop_table('citations')

    op.drop_column('messages', 'latency_ms')
    op.drop_column('messages', 'token_count')
    op.drop_column('messages', 'model')
    op.drop_column('messages', 'role')

    op.drop_constraint('fk_chats_workspace_id', 'chats', type_='foreignkey')
    op.drop_constraint('fk_chats_user_id', 'chats', type_='foreignkey')
    op.drop_index(op.f('ix_chats_workspace_id'), table_name='chats')
    op.drop_index(op.f('ix_chats_user_id'), table_name='chats')
    op.drop_column('chats', 'settings')
    op.drop_column('chats', 'is_pinned')
    op.drop_column('chats', 'workspace_id')
    op.drop_column('chats', 'user_id')
