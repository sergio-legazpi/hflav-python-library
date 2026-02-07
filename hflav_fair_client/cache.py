import os
import requests_cache

from hflav_fair_client.config import Config, EnvironmentVariables
from hflav_fair_client.logger import get_logger

logger = get_logger(__name__)


def init_cache() -> None:
    """Initialize the requests cache for HTTP requests."""
    name = Config.get_variable(EnvironmentVariables.HFLAV_CACHE_NAME, "hflav_cache")
    expire_after = int(
        Config.get_variable(EnvironmentVariables.HFLAV_CACHE_EXPIRE_AFTER, "2592000")
    )
    requests_cache.install_cache(
        cache_name=name,
        backend="sqlite",
        expire_after=expire_after,
    )
    logger.info(f"Cache {requests_cache.get_cache().cache_name} initialized.")
