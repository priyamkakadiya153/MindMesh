"""Create cognitive_agent_memories table

Revision ID: 20260823000000
Revises: 20260822000000
Create Date: 2026-08-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260823000000'
down_revision = '20260822000000'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'cognitive_agent_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cognitive_agents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('memory_type', sa.String(length=30), nullable=False, server_default='EPISODIC', index=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE', index=True),
        sa.Column('key', sa.String(length=255), nullable=False, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True, server_default='0.9'),
        sa.Column('confidence_level', sa.String(length=30), nullable=False, server_default='CONFIRMED'),
        sa.Column('source_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cognitive_agent_executions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_output_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cognitive_agent_outputs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_entity_type', sa.String(length=50), nullable=True),
        sa.Column('source_entity_id', sa.String(length=255), nullable=True),
        sa.Column('superseded_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('expired_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true')
    )

def downgrade() -> None:
    op.drop_table('cognitive_agent_memories')
