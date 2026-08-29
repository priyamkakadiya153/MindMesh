"""project spec tables

Revision ID: 20260702000200
Revises: 20260702000100
Create Date: 2026-07-02 00:02:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260702000200'
down_revision: Union[str, None] = '20260702000100'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('projects', sa.Column('owner_id', sa.UUID(), nullable=True))
    op.add_column('projects', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('projects', sa.Column('icon', sa.String(50), nullable=True))
    op.add_column('projects', sa.Column('color', sa.String(7), nullable=True))
    op.add_column('projects', sa.Column('visibility', sa.String(20), nullable=False, server_default='private'))
    op.add_column('projects', sa.Column('status', sa.String(20), nullable=False, server_default='active'))
    op.add_column('projects', sa.Column('default_ai_model', sa.String(50), nullable=True))
    op.add_column('projects', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))

    with op.batch_alter_table('projects') as batch_op:
        batch_op.create_foreign_key('fk_projects_owner_id', 'users', ['owner_id'], ['id'], ondelete='SET NULL')

    op.add_column('project_members', sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))

def downgrade() -> None:
    op.drop_column('project_members', 'joined_at')

    with op.batch_alter_table('projects') as batch_op:
        batch_op.drop_constraint('fk_projects_owner_id', type_='foreignkey')

    op.drop_column('projects', 'is_archived')
    op.drop_column('projects', 'default_ai_model')
    op.drop_column('projects', 'status')
    op.drop_column('projects', 'visibility')
    op.drop_column('projects', 'color')
    op.drop_column('projects', 'icon')
    op.drop_column('projects', 'description')
    op.drop_column('projects', 'owner_id')
