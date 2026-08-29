import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.database.base import Base
# Import all models to ensure they register on Base.metadata
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.models.permission import Permission
from app.models.session import UserSession
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.favorite import Favorite
from app.models.recent_item import RecentItem
from app.models.document import Document, DocumentChunk
from app.models.chat import Chat
from app.models.message import Message
from app.models.task import Task
from app.models.agent import Agent, AgentMemory
from app.models.audit import AuditLog
from app.ai.embeddings.models import DocumentChunk, DocumentEmbedding
from app.vector.models import VectorIndex, EmbeddingJob
from app.memory.models import LongTermMemory, AgentFeedback, GovernancePolicy, AuditDecisionLog



target_metadata = Base.metadata


from app.core.config import settings

def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
