import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("."))

from app.core.database import engine
from sqlalchemy import text

async def apply_ddl():
    print("Applying Phase 1.0 Enterprise Auth & Knowledge System DDL Schema updates...")
    async with engine.begin() as conn:
        # Update users table
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS firebase_uid VARCHAR UNIQUE;'))
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS is_phone_verified BOOLEAN DEFAULT FALSE;'))
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE;'))
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;'))
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT \'UTC\';'))
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT \'en\';'))
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS theme VARCHAR(20) DEFAULT \'dark\';'))
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITHOUT TIME ZONE;'))

        # Create email_verifications table
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS email_verifications (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                email VARCHAR(255) NOT NULL,
                token VARCHAR(255) NOT NULL UNIQUE,
                code VARCHAR(10) NOT NULL,
                expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                is_used BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        # Create pending_registrations table
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS pending_registrations (
                id UUID PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                username VARCHAR(100) NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                phone_number VARCHAR(50) NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                registration_token VARCHAR(255) NOT NULL UNIQUE,
                otp_hash VARCHAR(255) NOT NULL,
                expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                is_used BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        # Create audit_logs table
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
                action VARCHAR(100) NOT NULL,
                details JSON NOT NULL DEFAULT '{}',
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))
        await conn.execute(text('ALTER TABLE audit_logs ALTER COLUMN organization_id DROP NOT NULL;'))

        # Update documents table
        await conn.execute(text('ALTER TABLE documents ADD COLUMN IF NOT EXISTS title VARCHAR(255);'))
        await conn.execute(text('ALTER TABLE documents ADD COLUMN IF NOT EXISTS original_filename VARCHAR(255);'))
        await conn.execute(text('ALTER TABLE documents ADD COLUMN IF NOT EXISTS stored_filename VARCHAR(255);'))
        await conn.execute(text('ALTER TABLE documents ADD COLUMN IF NOT EXISTS folder_id UUID REFERENCES folders(id) ON DELETE SET NULL;'))
        await conn.execute(text('ALTER TABLE documents ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE documents ALTER COLUMN project_id DROP NOT NULL;'))
        await conn.execute(text('ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL;'))

        # Update chats table
        await conn.execute(text('ALTER TABLE chats ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE chats ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE chats ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE;'))
        await conn.execute(text('ALTER TABLE chats ADD COLUMN IF NOT EXISTS settings JSON;'))
        await conn.execute(text('ALTER TABLE chats ADD COLUMN IF NOT EXISTS description TEXT;'))
        await conn.execute(text('ALTER TABLE chats ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT \'active\';'))
        await conn.execute(text('ALTER TABLE chats ADD COLUMN IF NOT EXISTS last_message_at TIMESTAMP WITHOUT TIME ZONE;'))

        # Update messages table
        await conn.execute(text('ALTER TABLE messages ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT \'user\';'))
        await conn.execute(text('ALTER TABLE messages ADD COLUMN IF NOT EXISTS content_type VARCHAR(50) NOT NULL DEFAULT \'text/plain\';'))
        await conn.execute(text('ALTER TABLE messages ADD COLUMN IF NOT EXISTS msg_metadata JSON;'))
        await conn.execute(text('ALTER TABLE messages ADD COLUMN IF NOT EXISTS model VARCHAR(100);'))
        await conn.execute(text('ALTER TABLE messages ADD COLUMN IF NOT EXISTS token_count INTEGER DEFAULT 0;'))
        await conn.execute(text('ALTER TABLE messages ADD COLUMN IF NOT EXISTS latency_ms INTEGER DEFAULT 0;'))

        # Update document_chunks table
        await conn.execute(text('ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS page_number INTEGER;'))
        await conn.execute(text('ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS section_title VARCHAR(255);'))
        await conn.execute(text('ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS character_count INTEGER NOT NULL DEFAULT 0;'))
        await conn.execute(text('ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS checksum VARCHAR(64) NOT NULL DEFAULT \'\';'))

        # Update document_embeddings table
        await conn.execute(text('ALTER TABLE document_embeddings ADD COLUMN IF NOT EXISTS document_id UUID REFERENCES documents(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE document_embeddings ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE document_embeddings ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE document_embeddings ADD COLUMN IF NOT EXISTS embedding_version INTEGER NOT NULL DEFAULT 1;'))

        # Create workspace_ai_settings table
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS workspace_ai_settings (
                id UUID PRIMARY KEY,
                workspace_id UUID NOT NULL UNIQUE REFERENCES workspaces(id) ON DELETE CASCADE,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                provider VARCHAR(50) NOT NULL DEFAULT 'gemini',
                model VARCHAR(100) NOT NULL DEFAULT 'gemini-2.5-flash',
                temperature DOUBLE PRECISION NOT NULL DEFAULT 0.7,
                top_p DOUBLE PRECISION NOT NULL DEFAULT 0.95,
                max_tokens INTEGER NOT NULL DEFAULT 2048,
                fallback_provider VARCHAR(50) NOT NULL DEFAULT 'openai',
                fallback_model VARCHAR(100) NOT NULL DEFAULT 'gpt-4o-mini',
                system_prompt TEXT,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        # Create citations table
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS citations (
                id UUID PRIMARY KEY,
                message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
                conversation_id UUID REFERENCES chats(id) ON DELETE CASCADE,
                document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                page_number INTEGER,
                section_title VARCHAR(255),
                similarity_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                confidence_score VARCHAR(20) NOT NULL DEFAULT 'High',
                citation_order INTEGER NOT NULL DEFAULT 1,
                citation_tag VARCHAR(10) NOT NULL DEFAULT '[1]',
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('ALTER TABLE citations ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES chats(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE citations ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE citations ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE citations ADD COLUMN IF NOT EXISTS section_title VARCHAR(255);'))
        await conn.execute(text('ALTER TABLE citations ADD COLUMN IF NOT EXISTS similarity_score DOUBLE PRECISION NOT NULL DEFAULT 0.0;'))
        await conn.execute(text('ALTER TABLE citations ADD COLUMN IF NOT EXISTS confidence_score VARCHAR(20) NOT NULL DEFAULT \'High\';'))
        await conn.execute(text('ALTER TABLE citations ADD COLUMN IF NOT EXISTS citation_order INTEGER NOT NULL DEFAULT 1;'))
        await conn.execute(text('ALTER TABLE citations ADD COLUMN IF NOT EXISTS citation_tag VARCHAR(10) NOT NULL DEFAULT \'[1]\';'))

        # Create conversation_summaries table
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                id UUID PRIMARY KEY,
                conversation_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                summary TEXT NOT NULL,
                message_range_start INTEGER NOT NULL DEFAULT 1,
                message_range_end INTEGER NOT NULL DEFAULT 1,
                key_decisions JSON,
                action_items JSON,
                topics JSON,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        # Create conversation_memories table
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS conversation_memories (
                id UUID PRIMARY KEY,
                chat_id UUID REFERENCES chats(id) ON DELETE CASCADE,
                conversation_id UUID REFERENCES chats(id) ON DELETE CASCADE,
                workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                memory_type VARCHAR(50) NOT NULL DEFAULT 'fact',
                importance INTEGER NOT NULL DEFAULT 3,
                content TEXT NOT NULL,
                metadata_json JSON,
                is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
                expiration_status VARCHAR(20) NOT NULL DEFAULT 'permanent',
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('ALTER TABLE conversation_memories ALTER COLUMN chat_id DROP NOT NULL;'))
        await conn.execute(text('ALTER TABLE conversation_memories ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES chats(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE conversation_memories ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE conversation_memories ADD COLUMN IF NOT EXISTS memory_type VARCHAR(50) NOT NULL DEFAULT \'fact\';'))
        await conn.execute(text('ALTER TABLE conversation_memories ADD COLUMN IF NOT EXISTS importance INTEGER NOT NULL DEFAULT 3;'))
        await conn.execute(text('ALTER TABLE conversation_memories ADD COLUMN IF NOT EXISTS content TEXT NOT NULL DEFAULT \'\';'))
        await conn.execute(text('ALTER TABLE conversation_memories ADD COLUMN IF NOT EXISTS metadata_json JSON;'))
        await conn.execute(text('ALTER TABLE conversation_memories ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN NOT NULL DEFAULT FALSE;'))
        await conn.execute(text('ALTER TABLE conversation_memories ADD COLUMN IF NOT EXISTS expiration_status VARCHAR(20) NOT NULL DEFAULT \'permanent\';'))

        # Phase 2.0 Organization & Workspace Multi-Tenant DDL Schema Updates
        await conn.execute(text('ALTER TABLE organizations ADD COLUMN IF NOT EXISTS website VARCHAR(255);'))
        await conn.execute(text('ALTER TABLE organizations ADD COLUMN IF NOT EXISTS industry VARCHAR(100);'))
        await conn.execute(text('ALTER TABLE organizations ADD COLUMN IF NOT EXISTS country VARCHAR(100);'))
        await conn.execute(text('ALTER TABLE organizations ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT \'UTC\';'))
        await conn.execute(text('ALTER TABLE organizations ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT \'en\';'))
        await conn.execute(text('ALTER TABLE organizations ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT \'active\';'))
        await conn.execute(text('ALTER TABLE organizations ADD COLUMN IF NOT EXISTS visibility VARCHAR(50) DEFAULT \'private\';'))
        await conn.execute(text('ALTER TABLE organizations ADD COLUMN IF NOT EXISTS is_personal BOOLEAN DEFAULT FALSE;'))
        await conn.execute(text('ALTER TABLE organizations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITHOUT TIME ZONE;'))

        await conn.execute(text('ALTER TABLE organization_members ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT \'member\';'))
        await conn.execute(text('ALTER TABLE organization_members ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT \'active\';'))
        await conn.execute(text('ALTER TABLE organization_members ADD COLUMN IF NOT EXISTS joined_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();'))
        await conn.execute(text('ALTER TABLE organization_members ALTER COLUMN role_id DROP NOT NULL;'))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS organization_settings (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL UNIQUE REFERENCES organizations(id) ON DELETE CASCADE,
                default_language VARCHAR(10) NOT NULL DEFAULT 'en',
                timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
                theme VARCHAR(20) NOT NULL DEFAULT 'dark',
                branding_color VARCHAR(20) NOT NULL DEFAULT '#3B82F6',
                allow_public_invites BOOLEAN NOT NULL DEFAULT FALSE,
                allow_guest_access BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS organization_invitations (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                email VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'member',
                token VARCHAR(255) NOT NULL UNIQUE,
                invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS icon VARCHAR(50);'))
        await conn.execute(text('ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS color VARCHAR(20) DEFAULT \'#3B82F6\';'))
        await conn.execute(text('ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES users(id) ON DELETE SET NULL;'))
        await conn.execute(text('ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT \'active\';'))
        await conn.execute(text('ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE;'))
        await conn.execute(text('ALTER TABLE workspaces ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITHOUT TIME ZONE;'))

        await conn.execute(text('ALTER TABLE workspace_members ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT \'active\';'))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS workspace_settings (
                id UUID PRIMARY KEY,
                workspace_id UUID NOT NULL UNIQUE REFERENCES workspaces(id) ON DELETE CASCADE,
                theme VARCHAR(20) NOT NULL DEFAULT 'dark',
                timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
                language VARCHAR(10) NOT NULL DEFAULT 'en',
                default_dashboard VARCHAR(50) NOT NULL DEFAULT 'overview',
                allow_ai BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text("ALTER TABLE workspace_settings ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) DEFAULT 'private';"))
        await conn.execute(text("ALTER TABLE workspace_settings ADD COLUMN IF NOT EXISTS default_ai_model VARCHAR(50) DEFAULT 'gemini-2.5-flash';"))
        await conn.execute(text("ALTER TABLE workspace_settings ADD COLUMN IF NOT EXISTS auto_index_files BOOLEAN DEFAULT TRUE;"))
        await conn.execute(text("ALTER TABLE workspace_settings ADD COLUMN IF NOT EXISTS enable_semantic_search BOOLEAN DEFAULT TRUE;"))
        await conn.execute(text("ALTER TABLE workspace_settings ADD COLUMN IF NOT EXISTS enable_ai_chat BOOLEAN DEFAULT TRUE;"))

        await conn.execute(text("ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS mentions BOOLEAN DEFAULT TRUE;"))
        await conn.execute(text("ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS project_updates BOOLEAN DEFAULT TRUE;"))

        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_organizations_slug ON organizations (slug);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_organizations_owner ON organizations (owner_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_org_members_user_org ON organization_members (user_id, organization_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_workspaces_org ON workspaces (organization_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_ws_members_user_ws ON workspace_members (user_id, workspace_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_org_invites_email ON organization_invitations (email);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_org_invites_token ON organization_invitations (token);'))

        # Phase 2.3 Projects Schema
        await conn.execute(text('ALTER TABLE projects ADD COLUMN IF NOT EXISTS start_date TIMESTAMP WITHOUT TIME ZONE;'))
        await conn.execute(text('ALTER TABLE projects ADD COLUMN IF NOT EXISTS end_date TIMESTAMP WITHOUT TIME ZONE;'))
        await conn.execute(text('ALTER TABLE projects ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITHOUT TIME ZONE;'))
        await conn.execute(text('ALTER TABLE project_members ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT \'active\';'))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS project_settings (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
                allow_external_sharing BOOLEAN NOT NULL DEFAULT FALSE,
                default_view VARCHAR(50) NOT NULL DEFAULT 'overview',
                enable_ai BOOLEAN NOT NULL DEFAULT TRUE,
                notification_level VARCHAR(50) NOT NULL DEFAULT 'all',
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_projects_workspace ON projects (workspace_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_projects_org ON projects (organization_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_projects_owner ON projects (owner_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_projects_status ON projects (status);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_projects_slug ON projects (slug);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_proj_members_user_proj ON project_members (user_id, project_id);'))

        # Phase 2.4 Unified Invitations Schema
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS invitations (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
                project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                email VARCHAR(255) NOT NULL,
                mobile VARCHAR(50),
                role VARCHAR(50) NOT NULL DEFAULT 'member',
                token VARCHAR(255) NOT NULL UNIQUE,
                invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        # Phase 2.4 Join Requests Schema
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS join_requests (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
                project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                message TEXT,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        # Phase 2.4 Permission Matrix Schema
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS permission_roles (
                id UUID PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE,
                level VARCHAR(50) NOT NULL DEFAULT 'organization',
                description TEXT,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS permission_matrix (
                id UUID PRIMARY KEY,
                role_name VARCHAR(50) NOT NULL,
                permission_key VARCHAR(100) NOT NULL,
                is_granted BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
            );
        '''))

        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_invitations_scope ON invitations (organization_id, workspace_id, project_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_invitations_email_token ON invitations (email, token);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_join_requests_user_org ON join_requests (user_id, organization_id, status);'))

        # Phase 2.5 RBAC & Permission Engine Schema
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS user_roles (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
                organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
                workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
                project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS permission_cache (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                cached_permissions TEXT NOT NULL,
                expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
            );
        '''))

        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_user_roles_user_org ON user_roles (user_id, organization_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_perm_cache_user_org ON permission_cache (user_id, organization_id);'))

        # Phase 2.6 Enterprise Settings & Audit Schema
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                theme VARCHAR(20) NOT NULL DEFAULT 'dark',
                language VARCHAR(10) NOT NULL DEFAULT 'en',
                timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
                email_notifications BOOLEAN NOT NULL DEFAULT TRUE,
                in_app_notifications BOOLEAN NOT NULL DEFAULT TRUE,
                privacy_level VARCHAR(20) NOT NULL DEFAULT 'standard',
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS notification_preferences (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                mentions BOOLEAN NOT NULL DEFAULT TRUE,
                project_updates BOOLEAN NOT NULL DEFAULT TRUE,
                workspace_updates BOOLEAN NOT NULL DEFAULT TRUE,
                marketing BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
            );
        '''))

        await conn.execute(text('ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS resource_type VARCHAR(50);'))
        await conn.execute(text('ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS resource_id VARCHAR(100);'))
        await conn.execute(text('ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_audit_logs_org_user ON audit_logs (organization_id, user_id, action);'))

        # Phase 2.7 Enterprise Dashboard, Activity & Search Index Schema
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
                project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                action VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50),
                entity_id VARCHAR(100),
                details TEXT,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS recent_items (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
                item_type VARCHAR(50) NOT NULL,
                item_id VARCHAR(100) NOT NULL,
                title VARCHAR(255) NOT NULL,
                subtitle VARCHAR(255),
                url VARCHAR(255),
                last_accessed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS search_index (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
                project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                content TEXT,
                item_type VARCHAR(50) NOT NULL,
                item_id VARCHAR(100) NOT NULL,
                url VARCHAR(255),
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
            );
        '''))

        await conn.execute(text('ALTER TABLE recent_items ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW();'))
        await conn.execute(text('ALTER TABLE recent_items ADD COLUMN IF NOT EXISTS item_type VARCHAR(50);'))
        await conn.execute(text('ALTER TABLE recent_items ADD COLUMN IF NOT EXISTS item_id VARCHAR(100);'))
        await conn.execute(text('ALTER TABLE recent_items ADD COLUMN IF NOT EXISTS title VARCHAR(255);'))
        await conn.execute(text('ALTER TABLE recent_items ADD COLUMN IF NOT EXISTS subtitle VARCHAR(255);'))
        await conn.execute(text('ALTER TABLE recent_items ADD COLUMN IF NOT EXISTS url VARCHAR(255);'))

        await conn.execute(text('ALTER TABLE search_index ADD COLUMN IF NOT EXISTS item_type VARCHAR(50);'))
        await conn.execute(text('ALTER TABLE search_index ADD COLUMN IF NOT EXISTS item_id VARCHAR(100);'))
        await conn.execute(text('ALTER TABLE search_index ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE search_index ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE search_index ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE;'))

        # Phase 2.8 Enterprise Platform Foundation Schema
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS notifications (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(50) NOT NULL DEFAULT 'info',
                priority VARCHAR(20) NOT NULL DEFAULT 'normal',
                is_read BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id UUID PRIMARY KEY,
                level VARCHAR(20) NOT NULL,
                module VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
            );
        '''))

        await conn.execute(text('ALTER TABLE notifications ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;'))
        await conn.execute(text('ALTER TABLE notifications ADD COLUMN IF NOT EXISTS type VARCHAR(50) DEFAULT \'info\';'))
        await conn.execute(text('ALTER TABLE notifications ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT \'normal\';'))
        await conn.execute(text('ALTER TABLE notifications ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE;'))
        await conn.execute(text('ALTER TABLE notifications ADD COLUMN IF NOT EXISTS link VARCHAR(500);'))
        await conn.execute(text('ALTER TABLE notifications ADD COLUMN IF NOT EXISTS entity_type VARCHAR(50);'))
        await conn.execute(text('ALTER TABLE notifications ADD COLUMN IF NOT EXISTS entity_id UUID;'))

        # Phase 3.1 One-to-One Messaging Schema
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
                project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
                type VARCHAR(30) NOT NULL DEFAULT 'private',
                name VARCHAR(255),
                description TEXT,
                participant_one UUID REFERENCES users(id) ON DELETE CASCADE,
                participant_two UUID REFERENCES users(id) ON DELETE CASCADE,
                last_message_id UUID,
                last_message_at TIMESTAMP WITHOUT TIME ZONE,
                created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                avatar_url VARCHAR(500),
                owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
                visibility VARCHAR(30) NOT NULL DEFAULT 'private',
                is_archived BOOLEAN NOT NULL DEFAULT FALSE,
                archived_at TIMESTAMP WITHOUT TIME ZONE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('ALTER TABLE conversations ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);'))
        await conn.execute(text('ALTER TABLE conversations ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES users(id) ON DELETE SET NULL;'))
        await conn.execute(text('ALTER TABLE conversations ADD COLUMN IF NOT EXISTS visibility VARCHAR(30) DEFAULT \'private\';'))
        await conn.execute(text('ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;'))
        await conn.execute(text('ALTER TABLE conversations ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITHOUT TIME ZONE;'))


        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS direct_messages (
                id UUID PRIMARY KEY,
                conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
                message_type VARCHAR(30) NOT NULL DEFAULT 'text',
                content TEXT NOT NULL,
                reply_to_id UUID REFERENCES direct_messages(id) ON DELETE SET NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'sent',
                edited BOOLEAN NOT NULL DEFAULT FALSE,
                deleted BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        # Add foreign key constraint for conversations.last_message_id referencing direct_messages.id
        await conn.execute(text('''
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'fk_conversations_last_message'
                ) THEN
                    ALTER TABLE conversations 
                    ADD CONSTRAINT fk_conversations_last_message 
                    FOREIGN KEY (last_message_id) REFERENCES direct_messages(id) ON DELETE SET NULL;
                END IF;
            END $$;
        '''))

        # Phase 3.4 Enterprise Attachments & File Sharing Schema
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS attachments (
                id UUID PRIMARY KEY,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
                conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
                message_id UUID REFERENCES direct_messages(id) ON DELETE SET NULL,
                uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                original_filename VARCHAR(255) NOT NULL,
                storage_filename VARCHAR(255) NOT NULL UNIQUE,
                mime_type VARCHAR(100) NOT NULL,
                file_size INT NOT NULL,
                checksum VARCHAR(64),
                storage_path TEXT NOT NULL,
                thumbnail_path TEXT,
                preview_path TEXT,
                version INT NOT NULL DEFAULT 1,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                download_count INT NOT NULL DEFAULT 0,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))
        await conn.execute(text('ALTER TABLE attachments ALTER COLUMN conversation_id DROP NOT NULL;'))
        await conn.execute(text('ALTER TABLE attachments ADD COLUMN IF NOT EXISTS folder_id UUID REFERENCES folders(id) ON DELETE SET NULL;'))
        await conn.execute(text('ALTER TABLE attachments ADD COLUMN IF NOT EXISTS tags JSONB;'))
        await conn.execute(text('ALTER TABLE attachments ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT \'ready\';'))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS attachment_versions (
                id UUID PRIMARY KEY,
                attachment_id UUID NOT NULL REFERENCES attachments(id) ON DELETE CASCADE,
                version_number INT NOT NULL,
                storage_filename VARCHAR(255) NOT NULL,
                file_size INT NOT NULL,
                checksum VARCHAR(64),
                storage_path TEXT NOT NULL,
                created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by_user VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS attachment_access_logs (
                id UUID PRIMARY KEY,
                attachment_id UUID NOT NULL REFERENCES attachments(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                action VARCHAR(30) NOT NULL,
                ip_address VARCHAR(50),
                accessed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))
        await conn.execute(text('ALTER TABLE direct_messages ADD COLUMN IF NOT EXISTS thread_count INT DEFAULT 0;'))
        await conn.execute(text('ALTER TABLE direct_messages ADD COLUMN IF NOT EXISTS last_reply_at TIMESTAMP WITHOUT TIME ZONE;'))
        await conn.execute(text('ALTER TABLE direct_messages ADD COLUMN IF NOT EXISTS forwarded_from_id UUID REFERENCES direct_messages(id) ON DELETE SET NULL;'))

        # Phase 3.5 Advanced Messaging Schema
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS message_reactions (
                id UUID PRIMARY KEY,
                message_id UUID NOT NULL REFERENCES direct_messages(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                emoji VARCHAR(30) NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                CONSTRAINT uq_message_user_emoji UNIQUE (message_id, user_id, emoji)
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS message_mentions (
                id UUID PRIMARY KEY,
                message_id UUID NOT NULL REFERENCES direct_messages(id) ON DELETE CASCADE,
                mentioned_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS pinned_messages (
                id UUID PRIMARY KEY,
                conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                message_id UUID NOT NULL REFERENCES direct_messages(id) ON DELETE CASCADE,
                pinned_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                pinned_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by_user VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                CONSTRAINT uq_conversation_pinned_message UNIQUE (conversation_id, message_id)
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS favorite_conversations (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                CONSTRAINT uq_user_favorite_conversation UNIQUE (user_id, conversation_id)
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS message_drafts (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                CONSTRAINT uq_user_conversation_draft UNIQUE (user_id, conversation_id)
            );
        '''))
        # Phase 3.6 Search DDL
        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS saved_searches (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                name VARCHAR(100) NOT NULL,
                query_text VARCHAR(500) NOT NULL,
                filters_json JSONB,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS recent_searches (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                query_text VARCHAR(500) NOT NULL,
                searched_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))




        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS conversation_members (
                id UUID PRIMARY KEY,
                conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL DEFAULT 'member',
                joined_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                last_read_message_id UUID REFERENCES direct_messages(id) ON DELETE SET NULL,
                last_read_at TIMESTAMP WITHOUT TIME ZONE,
                unread_count INTEGER NOT NULL DEFAULT 0,
                is_muted BOOLEAN NOT NULL DEFAULT FALSE,
                is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS message_reads (
                id UUID PRIMARY KEY,
                message_id UUID NOT NULL REFERENCES direct_messages(id) ON DELETE CASCADE,
                conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                read_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS typing_status (
                id UUID PRIMARY KEY,
                conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                is_typing BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('''
            CREATE TABLE IF NOT EXISTS user_presence (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                status VARCHAR(20) NOT NULL DEFAULT 'offline',
                custom_status VARCHAR(255),
                last_seen TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
                created_by VARCHAR,
                updated_by VARCHAR,
                deleted_at TIMESTAMP WITHOUT TIME ZONE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
        '''))

        await conn.execute(text('ALTER TABLE direct_messages ADD COLUMN IF NOT EXISTS client_msg_id VARCHAR(255);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_direct_messages_client_msg_id ON direct_messages (client_msg_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_conversations_org_type ON conversations (organization_id, type);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_conversations_participants ON conversations (participant_one, participant_two);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_direct_messages_conv_time ON direct_messages (conversation_id, created_at);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_conv_members_user ON conversation_members (user_id, conversation_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_user_presence_user ON user_presence (user_id);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_org_invitations_email_status ON organization_invitations (email, status);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_documents_org_ws_active ON documents (organization_id, workspace_id, is_active);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_chats_org_ws_active ON chats (organization_id, workspace_id, is_active);'))
        await conn.execute(text('CREATE INDEX IF NOT EXISTS ix_projects_org_ws_active ON projects (organization_id, workspace_id, is_active);'))

    print("DDL schema changes applied successfully!")

if __name__ == "__main__":
    asyncio.run(apply_ddl())




