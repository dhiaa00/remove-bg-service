from PIL import Image
from rembg import remove, new_session

from app.models.base import BackgroundRemover
from app.logging_config import get_logger

logger = get_logger(__name__)


class RembgRemover(BackgroundRemover):
    """
    Background remover using the rembg library.
    
    notes:
    - We use session reuse for performance (avoids reloading model per request)
    - Default model is 'u2net' - good general purpose
    """
    
    def __init__(self, model_name: str = "u2net"):
        """
        Initialize the rembg remover.
        
        Args:
            model_name: Which rembg model to use. Options include:
                - u2net: General purpose (default)
                - u2netp: Lightweight/fast version
                - isnet-general-use: Good for general images
        """
        self._model_name = model_name
        self._session = None
    
    @property
    def name(self) -> str:
        return "rembg"
    
    def initialize(self) -> None:
        """
        Pre-load the model by creating a session.
        
        The session caches the loaded model, so subsequent calls
        to remove() are much faster.
        """
        logger.info(f"Initializing rembg with model: {self._model_name}")
        try:
            self._session = new_session(self._model_name)
            logger.info("Rembg model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize rembg: {e}")
            raise RuntimeError(f"Failed to initialize rembg model: {e}") from e
    
    def remove_background(self, image: Image.Image) -> Image.Image:
        """
        Remove background using rembg.
        
        The rembg.remove() function handles:
        - Converting input to correct format
        - Running inference
        - Returning RGBA image with transparent background
        """
        if self._session is None:
            # Lazy initialization if not pre-loaded
            self.initialize()
        
        logger.debug("Processing image with rembg")
        try:
            # rembg.remove() accepts PIL Image and returns PIL Image
            result = remove(image, session=self._session)
            
            # Ensure output is RGBA
            if result.mode != "RGBA":
                result = result.convert("RGBA")
            
            logger.debug("Rembg processing complete")
            return result
            
        except Exception as e:
            logger.error(f"Rembg processing failed: {e}")
            raise RuntimeError(f"Background removal failed: {e}") from e
