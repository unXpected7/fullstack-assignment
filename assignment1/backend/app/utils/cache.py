from cachetools import TTLCache
from app.config.settings import settings

# Cache for product information
product_cache = TTLCache(maxsize=settings.cache_max_size, ttl=settings.cache_ttl)