"""add joined_at to workspace_members

Revision ID: 3195fc889c70
Revises: 20260706000000
Create Date: 2026-07-15 18:41:16.465248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3195fc889c70'
down_revision: Union[str, None] = '20260706000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('workspace_members', sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')))


def downgrade() -> None:
    op.drop_column('workspace_members', 'joined_at')
