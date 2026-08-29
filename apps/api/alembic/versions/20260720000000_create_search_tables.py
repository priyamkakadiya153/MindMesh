"""create search tables

Revision ID: 20260720000000
Revises: 20260719000000
Create Date: 2026-07-20 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260720000000'
down_revision: Union[str, None] = '20260719000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'search_index',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('owner_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_search_index_entity_type', 'search_index', ['entity_type'])
    op.create_index('ix_search_index_entity_id', 'search_index', ['entity_id'])
    op.create_index('ix_search_index_workspace_id', 'search_index', ['workspace_id'])
    op.create_index('ix_search_index_organization_id', 'search_index', ['organization_id'])
    op.create_index('ix_search_index_owner_id', 'search_index', ['owner_id'])
    op.create_index('idx_search_index_org_ws_type', 'search_index', ['organization_id', 'workspace_id', 'entity_type'])

    op.create_table(
        'search_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('query', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_search_history_user_id', 'search_history', ['user_id'])
    op.create_index('idx_search_history_user_created', 'search_history', ['user_id', 'created_at'])

def downgrade() -> None:
    op.drop_table('search_history')
    op.drop_table('search_index')
