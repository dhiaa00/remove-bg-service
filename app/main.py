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
    - Models are pre-downloaded during Docker build
    - Initialize models in background after server starts
    
    Shutdown:
    - Currently nothing, but could cleanup resources
    """
    # Startup
    logger.info("Starting background removal service...")
    
    # Important: Don't block server startup with model initialization
    # Server needs to bind to port ASAP for health checks
    # Initialize models in background after startup
    import asyncio
    
    async def init_models_background():
        """Initialize models in background after server starts."""
        # Give server time to bind to port first
        await asyncio.sleep(1)
        logger.info("Initializing models in background...")
        try:
            # Run in thread pool to not block event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, initialize_all_models)
            logger.info("Models initialized successfully")
        except Exception as e:
            logger.warning(f"Background model initialization failed: {e}")
            logger.info("Models will lazy-load on first request instead")
    
    # Start background initialization (don't await - let it run async)
    asyncio.create_task(init_models_background())
    logger.info("Server ready - models initializing in background")
    
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
