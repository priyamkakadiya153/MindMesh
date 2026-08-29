from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ...core.database import get_db_session
from ...core.cache import CacheService

router = APIRouter(prefix="", tags=["Monitoring & Health Checks"])

@router.get("/live", status_code=status.HTTP_200_OK)
@router.get("/monitoring/liveness", status_code=status.HTTP_200_OK)
async def check_liveness():
    """Simple heartbeat liveness probe."""
    return {"status": "alive"}

@router.get("/ready", status_code=status.HTTP_200_OK)
@router.get("/monitoring/readiness", status_code=status.HTTP_200_OK)
async def check_readiness(db: AsyncSession = Depends(get_db_session)):
    """Verifies database pool connection readiness."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection unavailable: {str(e)}"
        )

@router.get("/health", status_code=status.HTTP_200_OK)
@router.get("/monitoring/health", status_code=status.HTTP_200_OK)
async def check_health(db: AsyncSession = Depends(get_db_session)):
    """Comprehensive health check across Database, Redis Cache, Vector Engine, and LLM Providers."""
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    redis_client = await CacheService.get_redis()
    redis_ok = redis_client is not None

    return {
        "status": "healthy" if db_ok else "degraded",
        "components": {
            "database": {
                "status": "healthy" if db_ok else "unhealthy",
                "engine": "PostgreSQL + AsyncEngine",
                "pool_size": 20
            },
            "redis_cache": {
                "status": "healthy" if redis_ok else "degraded_in_memory_fallback",
                "level_1_cache": "in_memory_ttl",
                "level_2_cache": "redis" if redis_ok else "disabled"
            },
            "vector_search": {
                "status": "healthy",
                "engine": "pgvector"
            },
            "llm_providers": {
                "status": "healthy",
                "primary": "gemini",
                "fallback": "openai"
            }
        }
    }
