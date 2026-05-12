import hashlib
import asyncio
from collections import defaultdict
from cachetools import TTLCache

from typing import Any

from app.base.logger import logger


class MemoryCache:

    def __init__(self, maxsize: int = 100, ttl_seconds: int = 3600):
        self.cache = TTLCache[str, Any] (maxsize=maxsize, ttl=ttl_seconds)
        self.locks = defaultdict(asyncio.Lock)
        self.set_count = 0
        self.cleanup_interval = 100


    def _hash(self, value:str)->str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
    
    

    async def get_cache(self, key:str) -> Any | None:
        hash_key = self._hash(key)

        if hash_key in self.cache:
            logger.debug(f"Cache hit for key {key}")
            return self.cache[hash_key]
                

        async with self.locks[hash_key]:
            if hash_key in self.cache:
                logger.debug(f"Cache hit for key {key}")
                return self.cache[hash_key]

            return None
        


    async def set_cache(self, key:str, value:Any)->None:
        hash_key = self._hash(key)
        async with self.locks[hash_key]:
            logger.debug(f"Setting cache for key {key}")
            self.cache[hash_key] = value

        self.set_count += 1
        if self.set_count % self.cleanup_interval == 0:
            self.cleanup_locks()

    
    def cleanup_locks(self) -> None:
        # TTL이 지난 cache entry를 먼저 정리합니다.
        self.cache.expire()
        # locks에 있는 key중에 만료된 대상을 찾습니다.
        expired_keys = [
            key for key in self.locks.keys()
            if key not in self.cache
        ]

        for key in expired_keys:
            self.locks.pop(key, None)



        

memory_cache = MemoryCache()

