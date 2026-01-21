"""
Configuration management using pydantic-settings.
All configuration is loaded from environment variables with sensible defaults.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Logging
    log_level: str = "INFO"
    
    # File upload limits
    max_file_size_mb: int = 10
    allowed_extensions: set[str] = {"jpg", "jpeg", "png", "webp"}
    
    # Model settings
    default_model: str = "rembg"
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes for size validation."""
        return self.max_file_size_mb * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures we only parse environment once.
    """
    return Settings()
