import redis.asyncio as redis
from src.config import settings
from src.core.logging import logger

class RedisManager:
    def __init__(self):
        self.client: redis.Redis = None

    def initialize(self):
        """
        Create the async Redis connection client.
        """
        logger.info("Initializing async Redis client...", url=settings.REDIS_URL)
        self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def close(self):
        """
        Gracefully terminate Redis connections.
        """
        if self.client:
            logger.info("Closing Redis connection pool...")
            await self.client.close()

    async def ping(self) -> bool:
        """
        Checks Redis cache server connectivity.
        """
        if not self.client:
            return False
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error("Redis ping connectivity check failed", error=str(e))
            return False


redis_manager = RedisManager()
