"""workspace spec tables

Revision ID: 20260702000100
Revises: 20260702000000
Create Date: 2026-07-02 00:01:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260702000100'
down_revision: Union[str, None] = '20260702000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('workspaces', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('workspaces', sa.Column('icon', sa.String(50), nullable=True))
    op.add_column('workspaces', sa.Column('color', sa.String(7), nullable=True))
    op.add_column('workspaces', sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('workspaces', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))
    
    with op.batch_alter_table('workspaces') as batch_op:
        batch_op.drop_column('created_by')
        batch_op.add_column(sa.Column('created_by', sa.UUID(), nullable=True))
        batch_op.create_foreign_key('fk_workspaces_created_by', 'users', ['created_by'], ['id'], ondelete='SET NULL')

def downgrade() -> None:
    with op.batch_alter_table('workspaces') as batch_op:
        batch_op.drop_constraint('fk_workspaces_created_by', type_='foreignkey')
        batch_op.drop_column('created_by')
        batch_op.add_column(sa.Column('created_by', sa.String(), nullable=True))
        
    op.drop_column('workspaces', 'is_archived')
    op.drop_column('workspaces', 'is_default')
    op.drop_column('workspaces', 'color')
    op.drop_column('workspaces', 'icon')
    op.drop_column('workspaces', 'description')
