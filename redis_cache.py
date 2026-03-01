# redis_cache.py - Versión compatible con Render
import os
import json
from typing import Any, Optional, Dict
from collections import OrderedDict
import time

# Cache en memoria como fallback
class MemoryCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache: Dict[str, dict] = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            item = self._cache[key]
            if time.time() < item['expires']:
                self._cache.move_to_end(key)
                return item['data']
            else:
                del self._cache[key]
        return None

    def set(self, key: str, data: Any, expire: int = None) -> bool:
        if expire is None:
            expire = self.default_ttl
            
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
            
        self._cache[key] = {
            'data': data,
            'expires': time.time() + expire
        }
        return True

    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear_pattern(self, pattern: str) -> bool:
        keys_to_delete = [key for key in self._cache.keys() if pattern in key]
        for key in keys_to_delete:
            del self._cache[key]
        return True

    def health_check(self) -> bool:
        return True

    @property
    def redis_client(self):
        return self

    def keys(self, pattern: str = "*"):
        if pattern == "*":
            return list(self._cache.keys())
        return [key for key in self._cache.keys() if pattern in key]

# Intentar usar Redis si está disponible, sino usar memoria
try:
    import redis
    
    # Verificar si estamos en un entorno con Redis disponible
    REDIS_URL = os.getenv('REDIS_URL')
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    
    if REDIS_URL or REDIS_HOST != 'localhost':
        # Entorno de producción - intentar conectar a Redis externo
        class RedisCache:
            def __init__(self):
                if REDIS_URL:
                    # Para servicios como Redis Cloud, Heroku Redis, etc.
                    self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
                else:
                    self.redis_client = redis.Redis(
                        host=REDIS_HOST,
                        port=int(os.getenv('REDIS_PORT', 6379)),
                        db=int(os.getenv('REDIS_DB', 0)),
                        password=os.getenv('REDIS_PASSWORD'),
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5
                    )
                
            def get(self, key: str) -> Optional[Any]:
                try:
                    cached_data = self.redis_client.get(key)
                    if cached_data:
                        return json.loads(cached_data)
                    return None
                except Exception:
                    return None

            def set(self, key: str, data: Any, expire: int = 3600) -> bool:
                try:
                    self.redis_client.setex(
                        key, 
                        expire, 
                        json.dumps(data, default=str)
                    )
                    return True
                except Exception:
                    return False

            def delete(self, key: str) -> bool:
                try:
                    self.redis_client.delete(key)
                    return True
                except Exception:
                    return False

            def clear_pattern(self, pattern: str) -> bool:
                try:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                    return True
                except Exception:
                    return False

            def health_check(self) -> bool:
                try:
                    return self.redis_client.ping()
                except Exception:
                    return False

            def keys(self, pattern: str = "*"):
                try:
                    return self.redis_client.keys(pattern)
                except Exception:
                    return []
        
        cache = RedisCache()
        print("✅ Redis cache inicializado")
        
    else:
        # En localhost sin Redis, usar memoria
        cache = MemoryCache()
        print("✅ Cache en memoria inicializado (localhost sin Redis)")
        
except ImportError:
    # Redis no está instalado, usar memoria
    cache = MemoryCache()
    print("✅ Cache en memoria inicializado (redis no instalado)")