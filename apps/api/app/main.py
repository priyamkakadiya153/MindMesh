from fastapi import FastAPI, Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .database.session import get_session
from .lifespan import lifespan
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .api.v1 import router as v1_router
import time

from .authorization.middleware import AuthorizationMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.correlation import CorrelationIdMiddleware

app = FastAPI(
    title="MindMesh API Backend",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.NODE_ENV == "development" else None,
)

app.add_middleware(CorrelationIdMiddleware)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
app.add_middleware(RateLimitMiddleware, max_requests=10, window_seconds=60)
app.add_middleware(AuthorizationMiddleware)

import os

cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3002",
    "http://127.0.0.1:5173",
    "https://mindmesh-kappa.vercel.app",
]

cors_env = os.getenv("CORS_ORIGINS", "")
if cors_env:
    cors_origins.extend([o.strip() for o in cors_env.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.onrender\.com|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTPException",
            "message": exc.detail,
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg_parts = []
    for err in errors:
        loc_parts = [str(x) for x in err.get("loc", []) if str(x) not in ("body", "query", "path")]
        loc_str = " -> ".join(loc_parts)
        msg_parts.append(f"{loc_str}: {err.get('msg')}" if loc_str else err.get("msg", "Invalid parameter"))
    readable_message = "; ".join(msg_parts) if msg_parts else "Invalid request parameter payload"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": readable_message,
            "detail": readable_message,
            "details": errors,
            "status_code": 422,
            "timestamp": time.time()
        }
    )

import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.exception(f"[DATABASE EXCEPTION] {request.method} {request.url.path}: {exc}")
    detail_msg = f"Database error: {str(exc)}"
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "DatabaseError",
            "message": detail_msg,
            "detail": detail_msg,
            "status_code": 400,
            "timestamp": time.time()
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"[UNHANDLED EXCEPTION] {request.method} {request.url.path}: {exc}")
    user_msg = "An unexpected server error occurred. Please try again."
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": user_msg,
            "detail": user_msg,
            "status_code": 500,
            "timestamp": time.time()
        }
    )

from .websocket.router import router as websocket_router

# Register v1 API Router
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v1_router, prefix="/api")
app.include_router(websocket_router, prefix="")



@app.get("/")
@app.get("/api")
async def root_welcome():
    return {
        "status": "online",
        "service": "MindMesh API Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api_v1": "/api/v1"
    }

@app.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    try:
        await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "timestamp": time.time(),
        "service": "MindMesh API Backend (FastAPI - App Module)",
        "database": db_status
    }


