"""documents tables

Revision ID: 20260705000000
Revises: 20260702000300
Create Date: 2026-07-05 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '20260705000000'
down_revision: Union[str, None] = '20260702000300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS document_chunks CASCADE")
    op.execute("DROP TABLE IF EXISTS documents CASCADE")
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('uploaded_by', sa.UUID(), nullable=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('extension', sa.String(20), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('checksum_sha256', sa.String(64), nullable=False),
        sa.Column('storage_provider', sa.String(50), nullable=False, server_default='local'),
        sa.Column('storage_path', sa.String(1024), nullable=False),
        sa.Column('processing_status', sa.String(50), nullable=False, server_default='QUEUED'),
        sa.Column('visibility', sa.String(50), nullable=False, server_default='private'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('ix_documents_organization_id', 'documents', ['organization_id'])
    op.create_index('ix_documents_workspace_id', 'documents', ['workspace_id'])
    op.create_index('ix_documents_project_id', 'documents', ['project_id'])
    op.create_index('ix_documents_uploaded_by', 'documents', ['uploaded_by'])

    op.create_table(
        'document_upload_jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='QUEUED'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE')
    )
    op.create_index('ix_document_upload_jobs_document_id', 'document_upload_jobs', ['document_id'])

def downgrade() -> None:
    op.drop_index('ix_document_upload_jobs_document_id', 'document_upload_jobs')
    op.drop_table('document_upload_jobs')
    op.drop_index('ix_documents_uploaded_by', 'documents')
    op.drop_index('ix_documents_project_id', 'documents')
    op.drop_index('ix_documents_workspace_id', 'documents')
    op.drop_index('ix_documents_organization_id', 'documents')
    op.drop_table('documents')
