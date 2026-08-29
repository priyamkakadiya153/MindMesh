"""Add cognitive agent columns to proactive_suggestions

Revision ID: 20260822000000
Revises: 20260821000000
Create Date: 2026-08-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260822000000'
down_revision = '20260821000000'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('proactive_suggestions', sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('proactive_suggestions', sa.Column('agent_execution_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('proactive_suggestions', sa.Column('agent_output_id', postgresql.UUID(as_uuid=True), nullable=True))

def downgrade() -> None:
    op.drop_column('proactive_suggestions', 'agent_output_id')
    op.drop_column('proactive_suggestions', 'agent_execution_id')
    op.drop_column('proactive_suggestions', 'agent_id')
