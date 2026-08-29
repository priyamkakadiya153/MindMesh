"""document governance tables

Revision ID: 20260705000100
Revises: 20260705000000
Create Date: 2026-07-05 00:01:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260705000100'
down_revision: Union[str, None] = '20260705000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'document_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author', sa.String(255), nullable=True),
        sa.Column('language', sa.String(50), nullable=True, server_default='en'),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('labels', sa.JSON(), nullable=True),
        sa.Column('categories', sa.JSON(), nullable=True),
        sa.Column('department', sa.String(255), nullable=True),
        sa.Column('business_unit', sa.String(255), nullable=True),
        sa.Column('confidentiality', sa.String(50), nullable=False, server_default='internal'),
        sa.Column('custom_metadata', sa.JSON(), nullable=True),
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
    op.create_index('ix_document_metadata_document_id', 'document_metadata', ['document_id'])

    op.create_table(
        'document_versions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('storage_path', sa.String(1024), nullable=False),
        sa.Column('checksum_sha256', sa.String(64), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('uploaded_by', sa.UUID(), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('ix_document_versions_document_id', 'document_versions', ['document_id'])
    op.create_index('ix_document_versions_uploaded_by', 'document_versions', ['uploaded_by'])

    op.create_table(
        'document_audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('action_metadata', sa.JSON(), nullable=True),

        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('ix_document_audit_logs_document_id', 'document_audit_logs', ['document_id'])
    op.create_index('ix_document_audit_logs_user_id', 'document_audit_logs', ['user_id'])

    op.create_table(
        'retention_policies',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('retention_days', sa.Integer(), nullable=False),
        sa.Column('auto_archive', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_delete', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE')
    )
    op.create_index('ix_retention_policies_organization_id', 'retention_policies', ['organization_id'])

def downgrade() -> None:
    op.drop_index('ix_retention_policies_organization_id', 'retention_policies')
    op.drop_table('retention_policies')
    op.drop_index('ix_document_audit_logs_user_id', 'document_audit_logs')
    op.drop_index('ix_document_audit_logs_document_id', 'document_audit_logs')
    op.drop_table('document_audit_logs')
    op.drop_index('ix_document_versions_uploaded_by', 'document_versions')
    op.drop_index('ix_document_versions_document_id', 'document_versions')
    op.drop_table('document_versions')
    op.drop_index('ix_document_metadata_document_id', 'document_metadata')
    op.drop_table('document_metadata')
