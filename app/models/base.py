"""
Abstract base class for background removal models.
This defines the interface that all background removal implementations must follow.
"""
from abc import ABC, abstractmethod
from PIL import Image


class BackgroundRemover(ABC):
    """
    Abstract base class for background removal models.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique identifier for this model.
        Used in API to select which model to use.
        Example: "rembg", "withoutbg"
        """
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the model (load weights, warm up, etc).
        
        Called once at application startup. This separates the heavy
        loading work from individual requests, making first requests fast.
        
        Raises:
            RuntimeError: If model fails to initialize
        """
        pass
    
    @abstractmethod
    def remove_background(self, image: Image.Image) -> Image.Image:
        """
        Remove background from the input image.
        
        Args:
            image: PIL Image in any mode (RGB, RGBA, etc.)
            
        Returns:
            PIL Image in RGBA mode with transparent background
            
        Raises:
            RuntimeError: If background removal fails
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"
