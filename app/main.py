"""
Entry point
"""
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api import router
from app.config import get_settings
from app.logging_config import setup_logging, get_logger
from app.services.bg_removal import initialize_all_models

# Setup logging before anything else
setup_logging()
logger = get_logger(__name__)


async def background_model_initialization():
    """
    Initialize models in the background after the server starts.
    This allows healthchecks to pass immediately while models load.
    """
    # Wait a bit to ensure the server is fully started
    await asyncio.sleep(2)
    
    logger.info("Starting background model initialization...")
    try:
        initialize_all_models()
        logger.info("Background model initialization completed successfully")
    except Exception as e:
        logger.error(f"Background model initialization failed: {e}")
        logger.warning("Models will lazy-load on first request")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    
    Startup:
    - Start background task to initialize models AFTER healthcheck passes
    - This ensures fast startup and healthcheck response
    
    Shutdown:
    - Currently nothing, but could cleanup resources
    """
    # Startup
    logger.info("Starting background removal service...")
    settings = get_settings()
    logger.info(f"Server will listen on {settings.host}:{settings.port}")
    
    # Start model initialization in background (non-blocking)
    asyncio.create_task(background_model_initialization())
    logger.info("Background model initialization task started")
    
    yield  # App runs here
    
    # Shutdown
    logger.info("Shutting down background removal service...")


# Create FastAPI app
app = FastAPI(
    title="Background Removal API",
    version="1.0.0",
    lifespan=lifespan
)

# Include routes
app.include_router(router)


# Entry point for running directly
if __name__ == "__main__":
    settings = get_settings()
    
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,  # Disable in production, enable for development
        log_level=settings.log_level.lower()
    )
