import logging

import requests
from fastapi import APIRouter, Depends, HTTPException

from config.settings import NASA_API_KEY
from middleware.cache_auth import require_cache_admin
from redis_cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/asteroidDetails", tags=["Asteroid Details"])

API_NEO_SEARCH_URL = "https://api.nasa.gov/neo/rest/v1/neo/"
REQUEST_TIMEOUT = 15
CACHE_EXPIRE = 3600


def get_cache_key(asteroid_id: str) -> str:
    return f"asteroid_details:{asteroid_id}"


@router.get("/{asteroid_id}")
async def get_asteroid_details(asteroid_id: str):
    cache_key = get_cache_key(asteroid_id)
    cached_data = cache.get(cache_key)

    if cached_data:
        return {**cached_data, "source": "cache"}

    try:
        url = f"{API_NEO_SEARCH_URL}{asteroid_id}"
        params = {"api_key": NASA_API_KEY}

        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        asteroide = response.json()

        diametros_m = asteroide.get("estimated_diameter", {}).get("meters", {})
        diametro_min_m = diametros_m.get("estimated_diameter_min", 0)
        diametro_max_m = diametros_m.get("estimated_diameter_max", 0)

        if diametro_min_m > 0 and diametro_max_m > 0:
            diametro_promedio_m = (diametro_min_m + diametro_max_m) / 2
        else:
            diametro_promedio_m = 0

        close_approaches = asteroide.get("close_approach_data", [])
        ultimo_acercamiento = {}
        if close_approaches:
            mas_reciente = close_approaches[0]
            ultimo_acercamiento = {
                "fecha": mas_reciente.get("close_approach_date"),
                "velocidad_km_s": round(
                    float(
                        mas_reciente.get("relative_velocity", {}).get(
                            "kilometers_per_second", 0
                        )
                    ),
                    2,
                ),
                "distancia_km": round(
                    float(
                        mas_reciente.get("miss_distance", {}).get("kilometers", 0)
                    ),
                    2,
                ),
                "cuerpo_orbital": mas_reciente.get("orbiting_body"),
            }

        response_data = {
            "informacion_basica": {
                "id": asteroide.get("id"),
                "nombre": asteroide.get("name"),
                "enlace_nasa": asteroide.get("nasa_jpl_url"),
                "es_peligroso": asteroide.get(
                    "is_potentially_hazardous_asteroid", False
                ),
                "es_monitoreado": asteroide.get("is_sentry_object", False),
            },
            "tamano": {
                "diametro_minimo_metros": round(diametro_min_m, 2),
                "diametro_maximo_metros": round(diametro_max_m, 2),
                "comparacion": (
                    f"Aproximadamente {round(diametro_promedio_m, 2)} metros - "
                    f"similar a un edificio de {round(diametro_promedio_m / 3, 0)} pisos"
                    if diametro_promedio_m > 0
                    else "Tamaño no determinado"
                ),
            },
            "ultimo_acercamiento": ultimo_acercamiento,
            "datos_tecnicos": {
                "magnitud_absoluta": asteroide.get("absolute_magnitude_h"),
                "es_peligroso": asteroide.get(
                    "is_potentially_hazardous_asteroid", False
                ),
            },
        }

        cache.set(cache_key, response_data, CACHE_EXPIRE)

        return {**response_data, "source": "nasa_api"}
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        if status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Asteroide con ID '{asteroid_id}' no encontrado. "
                    "Verifica que el ID sea correcto."
                ),
            ) from exc

        logger.exception("Error HTTP al consultar el detalle del asteroide")
        raise HTTPException(
            status_code=status_code,
            detail="La API de NASA devolvió un error al consultar el asteroide.",
        ) from exc
    except requests.exceptions.RequestException as exc:
        logger.exception("Error de conexión al consultar el detalle del asteroide")
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar con la API de NASA.",
        ) from exc
    except Exception as exc:
        logger.exception("Error interno al consultar el detalle del asteroide")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor.",
        ) from exc


@router.delete(
    "/cache/{asteroid_id}",
    dependencies=[Depends(require_cache_admin)],
)
async def clear_asteroid_cache(asteroid_id: str):
    cache_key = get_cache_key(asteroid_id)
    if cache.delete(cache_key):
        return {"message": f"Caché del asteroide {asteroid_id} limpiado correctamente"}

    raise HTTPException(status_code=500, detail="No se pudo limpiar el caché")
