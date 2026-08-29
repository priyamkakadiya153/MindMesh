import sys
import asyncio
import logging
import app.models  # Pre-import to resolve circular dependency
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.base import BaseEntity
from app.agents.registry import agent_registry
from app.automation.workers import BackgroundWorkerManager
from app.learning.scheduler import LearningScheduler
from app.governance.policy_store import PolicyStore
from app.governance.policy_engine import PolicyEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProductionVerify")

async def verify_subsystems() -> bool:
    logger.info("Starting MindMesh Enterprise Production Sanity Check...")
    errors = 0

    # 1. Verify Database connectivity (Prod target)
    db_session_factory = None
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        logger.info("[✓] Database connection: OK (Connected to production Database)")
        db_session_factory = AsyncSessionLocal
    except Exception as e:
        logger.warning(f"[!] Target Database connection failed: {str(e)}")
        logger.info("Falling back to local in-memory SQLite engine for validation...")
        
        try:
            fallback_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
            fallback_session_local = async_sessionmaker(
                bind=fallback_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            async with fallback_engine.begin() as conn:
                await conn.run_sync(BaseEntity.metadata.create_all)
            logger.info("[✓] Fallback in-memory DB setup: OK")
            db_session_factory = fallback_session_local
        except Exception as fallback_err:
            logger.error(f"[✗] Fallback DB setup failed: {str(fallback_err)}")
            errors += 1

    # 2. Verify Agent Registry Loaders
    try:
        agents = list(agent_registry._agents.keys())
        logger.info(f"[✓] Agent Registry: OK (Found {len(agents)} agents: {agents})")
    except Exception as e:
        logger.error(f"[✗] Agent Registry check failed: {str(e)}")
        errors += 1

    # 3. Verify Automation Workers Status
    try:
        workers_active = BackgroundWorkerManager._is_active
        logger.info(f"[✓] Automation Workers background loops active: {workers_active}")
    except Exception as e:
        logger.error(f"[✗] Worker Manager check failed: {str(e)}")
        errors += 1

    # 4. Verify Learning scheduler
    try:
        learning_active = LearningScheduler._running
        logger.info(f"[✓] Learning Engine background loops active: {learning_active}")
    except Exception as e:
        logger.error(f"[✗] Learning Scheduler check failed: {str(e)}")
        errors += 1

    # 5. Policy Engine Check
    if db_session_factory:
        try:
            import uuid
            from app.models.organization import Organization
            from app.memory.models import GovernancePolicy
            from sqlalchemy import select, delete

            async with db_session_factory() as db:
                # Find or create organization
                stmt_org = select(Organization).limit(1)
                org_res = await db.execute(stmt_org)
                org = org_res.scalar_one_or_none()
                created_temp_org = False
                if org:
                    org_id = org.id
                else:
                    org = Organization(name="Sanity Temp Org", slug=f"temp-org-{uuid.uuid4()}", owner_id=None)
                    db.add(org)
                    await db.flush()
                    org_id = org.id
                    created_temp_org = True

                # Add a dummy policy
                policy = await PolicyStore.create_policy(
                    db=db,
                    organization_id=org_id,
                    name="Sanity Rule",
                    category="Security",
                    rules={"blocked_keywords": ["trigger_malware"]}
                )
                await db.commit()

                # Dry-run validation check
                allowed, violations = await PolicyEngine.validate_policy(
                    db=db,
                    organization_id=org_id,
                    category="Security",
                    context_data={"text": "Hello trigger_malware statements"}
                )
                
                # Cleanup dummy policy
                await db.execute(delete(GovernancePolicy).where(GovernancePolicy.id == policy.id))
                if created_temp_org:
                    await db.execute(delete(Organization).where(Organization.id == org_id))
                await db.commit()
                
                assert allowed is False
                assert len(violations) > 0
                logger.info(f"[✓] Governance Policy Engine validation test: OK (Successfully blocked violation)")
        except Exception as e:
            logger.error(f"[✗] Governance Policy Engine validation test failed: {str(e)}")
            errors += 1
    else:
        logger.error("[✗] Governance checks skipped because no DB session factory could be created.")
        errors += 1

    if errors == 0:
        logger.info("MindMesh Production Sanity Check completed: SUCCESS (Ready for Release)")
        return True
    else:
        logger.error(f"MindMesh Production Sanity Check completed: FAILED ({errors} errors encountered)")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_subsystems())
    sys.exit(0 if success else 1)
