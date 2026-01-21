"""Services package - business logic layer."""
from app.services.bg_removal import ModelRegistry, get_model, list_available_models

__all__ = ["ModelRegistry", "get_model", "list_available_models"]
