from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Shopping Cart API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./shopping_cart.db"

    # CORS
    cors_origins: list = ["*"]

    # Cache
    cache_ttl: int = 300  # 5 minutes
    cache_max_size: int = 1000

    # External Product Service
    product_service_timeout: float = 10.0

    # Security
    secret_key: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()