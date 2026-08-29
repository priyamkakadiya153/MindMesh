"""create otp_codes table

Revision ID: 20260802000000
Revises: 
Create Date: 2026-08-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '20260802000000'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""
        DO $$ 
        BEGIN 
            IF EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name='otp_codes'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='otp_codes' AND column_name='user_id'
            ) THEN
                DROP TABLE otp_codes CASCADE;
            END IF;
        END $$;

        CREATE TABLE IF NOT EXISTS otp_codes (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            otp_hash VARCHAR NOT NULL,
            purpose VARCHAR NOT NULL DEFAULT 'phone_login',
            expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            is_used BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITHOUT TIME ZONE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE
        );
        CREATE INDEX IF NOT EXISTS ix_otp_codes_user_id ON otp_codes(user_id);
    """)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS otp_codes CASCADE;")
