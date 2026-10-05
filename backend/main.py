"""Main FastAPI application entry point for Vibe Trader AI."""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.database.session import init_db
from app.api.v1.router import api_v1_router

# Setup logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vibe-trader-ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to handle startup and shutdown."""
    logger.info("Starting up Vibe Trader AI backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Configured CORS origins: {settings.CORS_ORIGINS}")
    
    # Initialize SQLite database and models
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as exc:
        logger.error(f"Database initialization failed: {exc}", exc_info=True)

    # Warm up local Qwen model into RAM asynchronously to avoid cold-start latency
    try:
        from app.services.market_assistant_service import MarketAssistantService
        MarketAssistantService.preload_model_in_background()
        logger.info("Triggered asynchronous background warm-up for local Qwen model.")
    except Exception as exc:
        logger.warning(f"Could not trigger Ollama preload: {exc}")
    
    yield
    
    logger.info("Shutting down Vibe Trader AI backend.")
    from app.services.market_assistant_service import MarketAssistantService
    if MarketAssistantService._ollama_client is not None:
        MarketAssistantService._ollama_client.close()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Local-first AI trading research & analysis backend for Forex, NSE, and MCX.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Strict CORS for local frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# HTTP Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# Global safe exception handler to avoid leaking internal debug tracebacks
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please verify backend logs.",
            "status": "error",
        },
    )

# Include v1 API router with /api prefix
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", summary="Root Status")
def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
        "market_demo": f"{settings.API_V1_PREFIX}/market/demo",
        "disclaimer": "DEMO DATA: Educational and research use only. Never triggers automated or live trades.",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
