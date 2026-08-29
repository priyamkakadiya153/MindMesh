"""Phase 3.1 Conversation Management schema update

Revision ID: 20260720000300
Revises: 20260720000200
Create Date: 2026-07-20 00:03:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260720000300'
down_revision: Union[str, None] = '20260720000200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add columns to chats table
    op.add_column('chats', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('chats', sa.Column('status', sa.String(length=50), nullable=False, server_default='active'))
    op.add_column('chats', sa.Column('last_message_at', sa.DateTime(), nullable=True))
    
    op.create_index(op.f('ix_chats_last_message_at'), 'chats', ['last_message_at'], unique=False)
    op.create_index(op.f('ix_chats_deleted_at'), 'chats', ['deleted_at'], unique=False)

    # Add columns to messages table
    op.add_column('messages', sa.Column('content_type', sa.String(length=50), nullable=False, server_default='text/plain'))
    op.add_column('messages', sa.Column('msg_metadata', sa.JSON(), nullable=True))
    
    op.create_index(op.f('ix_messages_created_at'), 'messages', ['created_at'], unique=False)
    op.create_index(op.f('ix_messages_deleted_at'), 'messages', ['deleted_at'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_messages_deleted_at'), table_name='messages')
    op.drop_index(op.f('ix_messages_created_at'), table_name='messages')
    op.drop_column('messages', 'msg_metadata')
    op.drop_column('messages', 'content_type')

    op.drop_index(op.f('ix_chats_deleted_at'), table_name='chats')
    op.drop_index(op.f('ix_chats_last_message_at'), table_name='chats')
    op.drop_column('chats', 'last_message_at')
    op.drop_column('chats', 'status')
    op.drop_column('chats', 'description')
