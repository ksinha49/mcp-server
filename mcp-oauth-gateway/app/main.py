"""
MCP OAuth Gateway - Main Application

Centralized OAuth service for MCP servers following MCP 2025-06-18 specification.

Endpoints:
- /.well-known/oauth-protected-resource.json - Protected Resource Metadata (RFC 9728)
- /oauth/authorize - Initiate OAuth authorization
- /oauth/callback/{provider} - OAuth callback handler
- /oauth/token - Token retrieval for authenticated users
- /oauth/refresh - Token refresh
- /oauth/revoke - Token revocation
- /health - Health check
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import oauth, well_known, admin
from mcp_oauth import init_oauth_state_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    settings = get_settings()

    # Initialize OAuth state manager
    log.info("Initializing OAuth state manager...")
    init_oauth_state_manager(
        redis_url=settings.redis_url,
        ttl_seconds=settings.oauth_state_ttl_seconds,
    )

    # Set TOKEN_ENCRYPTION_KEY in environment for mcp_oauth library
    if settings.token_encryption_key:
        import os
        os.environ["TOKEN_ENCRYPTION_KEY"] = settings.token_encryption_key

    log.info("MCP OAuth Gateway started at %s", settings.gateway_url)
    yield
    log.info("MCP OAuth Gateway shutting down...")


# Create FastAPI application
app = FastAPI(
    title="MCP OAuth Gateway",
    description="Centralized OAuth authorization service for MCP servers",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if get_settings().debug else None,
    redoc_url="/redoc" if get_settings().debug else None,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "MCP-Session-Id",
    ],
)


# Include routers
app.include_router(well_known.router)
app.include_router(oauth.router, prefix="/oauth", tags=["OAuth"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "mcp-oauth-gateway"}


@app.get("/ping", tags=["Health"])
async def ping():
    """Simple ping endpoint."""
    return "pong"


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    log.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "An unexpected error occurred"},
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
