"""
This module provides a clean way to register, retrieve, and manage
background removal models.
"""
from typing import Dict, Type

from app.models.base import BackgroundRemover
from app.models.rembg_model import RembgRemover
from app.models.withoutbg_model import WithoutBgRemover
from app.logging_config import get_logger

logger = get_logger(__name__)


class ModelRegistry:
    """
    Registry for background removal models.
    """
    
    def __init__(self):
        # Map of model name -> model class
        self._model_classes: Dict[str, Type[BackgroundRemover]] = {}
        # Map of model name -> initialized instance (lazy loaded)
        self._model_instances: Dict[str, BackgroundRemover] = {}
    
    def register(self, model_class: Type[BackgroundRemover]) -> None:
        """
        Register a model class.
        
        The model's name property is used as the key.
        Note: Creates a temporary instance to get the name.
        """
        # Create temporary instance to get name
        temp_instance = model_class()
        name = temp_instance.name
        self._model_classes[name] = model_class
        logger.debug(f"Registered model: {name}")
    
    def get(self, name: str) -> BackgroundRemover:
        """
        Get a model instance by name.
        
        Raises:
            ValueError: If model name is not registered
        """
        if name not in self._model_classes:
            available = ", ".join(self._model_classes.keys())
            raise ValueError(
                f"Unknown model: '{name}'. Available models: {available}"
            )
        
        # Lazy initialization - create instance on first access
        if name not in self._model_instances:
            logger.info(f"Creating instance of model: {name}")
            instance = self._model_classes[name]()
            self._model_instances[name] = instance
        
        return self._model_instances[name]
    
    def initialize_all(self) -> None:
        """
        Initialize all registered models.
        
        Called at application startup to pre-load models,
        making first requests faster.
        """
        logger.info("Initializing all registered models...")
        for name, model_class in self._model_classes.items():
            if name not in self._model_instances:
                instance = model_class()
                self._model_instances[name] = instance
            
            self._model_instances[name].initialize()
        
        logger.info(f"Initialized {len(self._model_instances)} models")
    
    def list_models(self) -> list[str]:
        """Get list of available model names."""
        return list(self._model_classes.keys())


# Global registry instance
# This is the singleton that the entire application uses
_registry = ModelRegistry()

# Register all available models
_registry.register(RembgRemover)
_registry.register(WithoutBgRemover)


# Public API - these functions are what other modules should use
def get_model(name: str) -> BackgroundRemover:
    """Get a model by name."""
    return _registry.get(name)


def list_available_models() -> list[str]:
    """Get list of available model names."""
    return _registry.list_models()


def initialize_all_models() -> None:
    """Initialize all models (call at startup)."""
    _registry.initialize_all()
