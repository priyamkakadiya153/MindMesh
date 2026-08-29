"""document management folders favorites shares

Revision ID: 20260720000100
Revises: 20260720000000
Create Date: 2026-07-20 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260720000100'
down_revision: Union[str, None] = '20260720000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create folders table
    op.create_table(
        'folders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['folders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('ix_folders_organization_id', 'folders', ['organization_id'])
    op.create_index('ix_folders_workspace_id', 'folders', ['workspace_id'])
    op.create_index('ix_folders_parent_id', 'folders', ['parent_id'])

    # 2. Add columns to documents if not existing
    try:
        op.add_column('documents', sa.Column('folder_id', sa.UUID(), nullable=True))
        op.create_foreign_key('fk_documents_folder_id', 'documents', 'folders', ['folder_id'], ['id'], ondelete='SET NULL')
        op.create_index('ix_documents_folder_id', 'documents', ['folder_id'])
    except Exception:
        pass

    try:
        op.add_column('documents', sa.Column('title', sa.String(255), nullable=True))
    except Exception:
        pass

    try:
        op.add_column('documents', sa.Column('stored_filename', sa.String(255), nullable=True))
    except Exception:
        pass

    # 3. Create document_favorites table
    op.create_table(
        'document_favorites',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE')
    )
    op.create_index('ix_document_favorites_user_id', 'document_favorites', ['user_id'])
    op.create_index('ix_document_favorites_document_id', 'document_favorites', ['document_id'])

    # 4. Create document_shares table
    op.create_table(
        'document_shares',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('shared_with_user_id', sa.UUID(), nullable=False),
        sa.Column('permission_level', sa.String(50), nullable=False, server_default='read'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_with_user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_document_shares_document_id', 'document_shares', ['document_id'])
    op.create_index('ix_document_shares_shared_with_user_id', 'document_shares', ['shared_with_user_id'])

def downgrade() -> None:
    op.drop_table('document_shares')
    op.drop_table('document_favorites')
    try:
        op.drop_constraint('fk_documents_folder_id', 'documents', type_='foreignkey')
        op.drop_column('documents', 'folder_id')
        op.drop_column('documents', 'title')
        op.drop_column('documents', 'stored_filename')
    except Exception:
        pass
    op.drop_table('folders')
