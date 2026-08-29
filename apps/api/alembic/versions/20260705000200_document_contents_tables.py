"""document contents tables

Revision ID: 20260705000200
Revises: 20260705000100
Create Date: 2026-07-05 00:02:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260705000200'
down_revision: Union[str, None] = '20260705000100'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'document_contents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('content_json', sa.JSON(), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=False),
        sa.Column('statistics', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('document_id')
    )
    op.create_index('ix_document_contents_document_id', 'document_contents', ['document_id'])

def downgrade() -> None:
    op.drop_index('ix_document_contents_document_id', 'document_contents')
    op.drop_table('document_contents')
