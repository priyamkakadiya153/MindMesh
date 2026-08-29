"""Phase 3.6 Multi-LLM Provider Abstraction & Workspace AI Settings schema

Revision ID: 20260721000300
Revises: 20260721000200
Create Date: 2026-07-21 00:03:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260721000300'
down_revision: Union[str, None] = '20260721000200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'workspace_ai_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='gemini'),
        sa.Column('model', sa.String(length=100), nullable=False, server_default='gemini-2.5-flash'),
        sa.Column('temperature', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('top_p', sa.Float(), nullable=False, server_default='0.95'),
        sa.Column('max_tokens', sa.Integer(), nullable=False, server_default='2048'),
        sa.Column('fallback_provider', sa.String(length=50), nullable=False, server_default='openai'),
        sa.Column('fallback_model', sa.String(length=100), nullable=False, server_default='gpt-4o-mini'),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id')
    )
    op.create_index(op.f('ix_workspace_ai_settings_workspace_id'), 'workspace_ai_settings', ['workspace_id'], unique=True)
    op.create_index(op.f('ix_workspace_ai_settings_organization_id'), 'workspace_ai_settings', ['organization_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_workspace_ai_settings_organization_id'), table_name='workspace_ai_settings')
    op.drop_index(op.f('ix_workspace_ai_settings_workspace_id'), table_name='workspace_ai_settings')
    op.drop_table('workspace_ai_settings')
