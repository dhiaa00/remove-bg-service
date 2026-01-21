"""
Entry point
"""
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    
    Startup:
    - Initialize all models (pre-load weights)
    
    Shutdown:
    - Currently nothing, but could cleanup resources
    """
    # Startup
    logger.info("Starting background removal service...")
    
    try:
        initialize_all_models()
        logger.info("All models initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize models: {e}")
        # Continue anyway - models will lazy-load on first request
    
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
