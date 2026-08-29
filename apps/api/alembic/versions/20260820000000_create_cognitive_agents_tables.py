"""create cognitive_agents tables

Revision ID: 20260820000000
Revises: 20260721000600
Create Date: 2026-08-20 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260820000000'
down_revision: Union[str, None] = '20260721000600'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create cognitive_agents table
    op.create_table(
        'cognitive_agents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=True),
        sa.Column('owner_user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('agent_type', sa.String(length=50), nullable=False, server_default='CUSTOM'),
        sa.Column('instructions', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='ACTIVE'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('knowledge_scope', sa.JSON(), nullable=True),
        sa.Column('triggers', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cognitive_agents_organization_id'), 'cognitive_agents', ['organization_id'], unique=False)
    op.create_index(op.f('ix_cognitive_agents_workspace_id'), 'cognitive_agents', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_cognitive_agents_owner_user_id'), 'cognitive_agents', ['owner_user_id'], unique=False)
    op.create_index(op.f('ix_cognitive_agents_status'), 'cognitive_agents', ['status'], unique=False)

    # 2. Create cognitive_agent_executions table
    op.create_table(
        'cognitive_agent_executions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('agent_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=True),
        sa.Column('triggered_by', sa.UUID(), nullable=True),
        sa.Column('trigger_type', sa.String(length=50), nullable=False, server_default='MANUAL'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='QUEUED'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('input_context', sa.JSON(), nullable=True),
        sa.Column('output_summary', sa.Text(), nullable=True),
        sa.Column('action_candidates_generated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['agent_id'], ['cognitive_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cognitive_agent_executions_agent_id'), 'cognitive_agent_executions', ['agent_id'], unique=False)
    op.create_index(op.f('ix_cognitive_agent_executions_organization_id'), 'cognitive_agent_executions', ['organization_id'], unique=False)
    op.create_index(op.f('ix_cognitive_agent_executions_workspace_id'), 'cognitive_agent_executions', ['workspace_id'], unique=False)
    op.create_index(op.f('ix_cognitive_agent_executions_status'), 'cognitive_agent_executions', ['status'], unique=False)

    # 3. Create cognitive_agent_outputs table
    op.create_table(
        'cognitive_agent_outputs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('execution_id', sa.UUID(), nullable=False),
        sa.Column('agent_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=True),
        sa.Column('output_type', sa.String(length=50), nullable=False, server_default='INSIGHT'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('candidate_type', sa.String(length=50), nullable=True),
        sa.Column('structured_payload', sa.JSON(), nullable=True),
        sa.Column('provenance', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['execution_id'], ['cognitive_agent_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['cognitive_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cognitive_agent_outputs_execution_id'), 'cognitive_agent_outputs', ['execution_id'], unique=False)
    op.create_index(op.f('ix_cognitive_agent_outputs_agent_id'), 'cognitive_agent_outputs', ['agent_id'], unique=False)
    op.create_index(op.f('ix_cognitive_agent_outputs_output_type'), 'cognitive_agent_outputs', ['output_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_cognitive_agent_outputs_output_type'), table_name='cognitive_agent_outputs')
    op.drop_index(op.f('ix_cognitive_agent_outputs_agent_id'), table_name='cognitive_agent_outputs')
    op.drop_index(op.f('ix_cognitive_agent_outputs_execution_id'), table_name='cognitive_agent_outputs')
    op.drop_table('cognitive_agent_outputs')

    op.drop_index(op.f('ix_cognitive_agent_executions_status'), table_name='cognitive_agent_executions')
    op.drop_index(op.f('ix_cognitive_agent_executions_workspace_id'), table_name='cognitive_agent_executions')
    op.drop_index(op.f('ix_cognitive_agent_executions_organization_id'), table_name='cognitive_agent_executions')
    op.drop_index(op.f('ix_cognitive_agent_executions_agent_id'), table_name='cognitive_agent_executions')
    op.drop_table('cognitive_agent_executions')

    op.drop_index(op.f('ix_cognitive_agents_status'), table_name='cognitive_agents')
    op.drop_index(op.f('ix_cognitive_agents_owner_user_id'), table_name='cognitive_agents')
    op.drop_index(op.f('ix_cognitive_agents_workspace_id'), table_name='cognitive_agents')
    op.drop_index(op.f('ix_cognitive_agents_organization_id'), table_name='cognitive_agents')
    op.drop_table('cognitive_agents')
