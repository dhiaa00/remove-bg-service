from PIL import Image
from withoutbg import WithoutBG

from app.models.base import BackgroundRemover
from app.logging_config import get_logger

logger = get_logger(__name__)


class WithoutBgRemover(BackgroundRemover):
    """
    Background remover using the withoutbg library
    
    notes:
    - Uses WithoutBG.opensource() for free local processing
    - Model is ~320MB, downloaded on first use
    - Returns PIL Image directly
    """
    
    def __init__(self):
        self._model = None
    
    @property
    def name(self) -> str:
        return "withoutbg"
    
    def initialize(self) -> None:
        """
        Pre-load the withoutbg model.
        
        First initialization downloads the model (~320MB) from HuggingFace.
        Subsequent initializations use cached model.
        """
        logger.info("Initializing withoutbg opensource model")
        try:
            self._model = WithoutBG.opensource()
            logger.info("WithoutBG model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize withoutbg: {e}")
            raise RuntimeError(f"Failed to initialize withoutbg model: {e}") from e
    
    def remove_background(self, image: Image.Image) -> Image.Image:
        """
        Remove background using withoutbg.
        
        The withoutbg library expects a file path or PIL Image.
        We pass the PIL Image directly.
        """
        if self._model is None:
            # Lazy initialization if not pre-loaded
            logger.info("WithoutBG model not pre-loaded, initializing now...")
            logger.warning("This may take 1-2 minutes and use significant memory")
            self.initialize()
        
        logger.debug("Processing image with withoutbg")
        try:
            # Force garbage collection before processing to free memory
            import gc
            gc.collect()
            
            # withoutbg can accept PIL Image directly
            # It returns a PIL Image with transparent background
            result = self._model.remove_background(image)
            
            # Ensure output is RGBA
            if result.mode != "RGBA":
                result = result.convert("RGBA")
            
            logger.debug("WithoutBG processing complete")
            return result
            
        except Exception as e:
            logger.error(f"WithoutBG processing failed: {e}", exc_info=True)
            raise RuntimeError(f"Background removal failed: {e}") from e
