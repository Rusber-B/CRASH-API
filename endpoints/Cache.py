from fastapi import APIRouter, Depends, HTTPException, Query

from middleware.cache_auth import require_cache_admin
from redis_cache import cache

router = APIRouter(prefix="/cache", tags=["Cache"])


@router.get("/health")
async def cache_health():
    is_healthy = cache.health_check()
    return {
        "redis_connected": is_healthy,
        "status": "healthy" if is_healthy else "unhealthy",
    }


@router.get("/keys", dependencies=[Depends(require_cache_admin)])
async def get_cache_keys(pattern: str = Query(default="*", max_length=100)):
    try:
        keys = list(cache.keys(pattern))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudieron obtener las claves del caché",
        ) from exc

    return {"keys": keys, "count": len(keys)}


@router.delete("/clear", dependencies=[Depends(require_cache_admin)])
async def clear_cache(pattern: str = Query(default="*", max_length=100)):
    try:
        success = cache.clear_pattern(pattern)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo limpiar el caché",
        ) from exc

    if not success:
        raise HTTPException(status_code=500, detail="No se pudo limpiar el caché")

    return {"message": f"Caché limpiado para el patrón: {pattern}"}


@router.get("/info", dependencies=[Depends(require_cache_admin)])
async def get_cache_info():
    try:
        info = cache.info()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo obtener información del caché",
        ) from exc

    hits = info.get("keyspace_hits", 0)
    misses = info.get("keyspace_misses", 0)

    return {
        "backend": info.get("backend", "redis"),
        "connected_clients": info.get("connected_clients"),
        "used_memory_human": info.get("used_memory_human"),
        "used_memory_peak_human": info.get("used_memory_peak_human"),
        "keyspace_hits": hits,
        "keyspace_misses": misses,
        "hit_rate": hits / max(hits + misses, 1),
    }
