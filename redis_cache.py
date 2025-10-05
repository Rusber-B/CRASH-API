# redis_cache.py
import redis
import json
import os
from typing import Any, Optional

class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=True,
            password=os.getenv('REDIS_PASSWORD', None),
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )

    def get(self, key: str) -> Optional[Any]:
        """Obtiene datos del cache"""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except (redis.RedisError, json.JSONDecodeError):
            return None

    def set(self, key: str, data: Any, expire: int = 3600) -> bool:
        """Guarda datos en el cache"""
        try:
            self.redis_client.setex(
                key, 
                expire, 
                json.dumps(data, default=str)
            )
            return True
        except (redis.RedisError, TypeError):
            return False

    def delete(self, key: str) -> bool:
        """Elimina datos del cache"""
        try:
            self.redis_client.delete(key)
            return True
        except redis.RedisError:
            return False

    def clear_pattern(self, pattern: str) -> bool:
        """Elimina todas las keys que coincidan con el patrón"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except redis.RedisError:
            return False

    def health_check(self) -> bool:
        """Verifica que Redis esté funcionando"""
        try:
            return self.redis_client.ping()
        except redis.RedisError:
            return False

# Instancia global del cache
cache = RedisCache()