"""create cognitive_agent_triggers table

Revision ID: 20260821000000
Revises: 20260820000000
Create Date: 2026-08-21 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260821000000'
down_revision: Union[str, None] = '20260820000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'cognitive_agent_triggers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('agent_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=True),
        sa.Column('created_by_user_id', sa.UUID(), nullable=True),
        sa.Column('trigger_type', sa.String(length=30), nullable=False, server_default='SCHEDULE'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
        sa.Column('schedule_type', sa.String(length=30), nullable=True),
        sa.Column('time_str', sa.String(length=20), nullable=True),
        sa.Column('day_of_week', sa.String(length=20), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='Asia/Kolkata'),
        sa.Column('event_type', sa.String(length=50), nullable=True),
        sa.Column('event_filters', sa.JSON(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('last_execution_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['agent_id'], ['cognitive_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['last_execution_id'], ['cognitive_agent_executions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(op.f('ix_cognitive_agent_triggers_agent_id'), 'cognitive_agent_triggers', ['agent_id'], unique=False)
    op.create_index(op.f('ix_cognitive_agent_triggers_organization_id'), 'cognitive_agent_triggers', ['organization_id'], unique=False)
    op.create_index(op.f('ix_cognitive_agent_triggers_workspace_id'), 'cognitive_agent_triggers', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_cognitive_agent_triggers_trigger_type'), 'cognitive_agent_triggers', ['trigger_type'], unique=False)
    op.create_index(op.f('ix_cognitive_agent_triggers_status'), 'cognitive_agent_triggers', ['status'], unique=False)
    op.create_index(op.f('ix_cognitive_agent_triggers_event_type'), 'cognitive_agent_triggers', ['event_type'], unique=False)
    op.create_index(op.f('ix_cognitive_agent_triggers_next_run_at'), 'cognitive_agent_triggers', ['next_run_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_cognitive_agent_triggers_next_run_at'), table_name='cognitive_agent_triggers')
    op.drop_index(op.f('ix_cognitive_agent_triggers_event_type'), table_name='cognitive_agent_triggers')
    op.drop_index(op.f('ix_cognitive_agent_triggers_status'), table_name='cognitive_agent_triggers')
    op.drop_index(op.f('ix_cognitive_agent_triggers_trigger_type'), table_name='cognitive_agent_triggers')
    op.drop_index(op.f('ix_cognitive_agent_triggers_workspace_id'), table_name='cognitive_agent_triggers')
    op.drop_index(op.f('ix_cognitive_agent_triggers_organization_id'), table_name='cognitive_agent_triggers')
    op.drop_index(op.f('ix_cognitive_agent_triggers_agent_id'), table_name='cognitive_agent_triggers')
    op.drop_table('cognitive_agent_triggers')
