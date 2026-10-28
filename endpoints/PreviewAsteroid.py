import logging
import math
from datetime import date

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response

from config.settings import NASA_API_KEY
from middleware.cache_auth import require_cache_admin
from redis_cache import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/previewAsteroid", tags=["Preview Asteroid"])

API_NEO_FEED_URL = "https://api.nasa.gov/neo/rest/v1/feed"
API_SBDB_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api"
REQUEST_TIMEOUT = 15

CACHE_EXPIRE = 1800
EMPTY_RESULT_CACHE_EXPIRE = 600


def get_cache_key(fecha_consulta: str) -> str:
    return f"preview_asteroid:{fecha_consulta}"


def clean_asteroid_name(name: str) -> str:
    return name.replace("(", "").replace(")", "")


def get_sbdb_data(asteroid_name: str):
    try:
        response = requests.get(
            API_SBDB_URL,
            params={"sstr": clean_asteroid_name(asteroid_name)},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        logger.warning("No se pudieron obtener datos SBDB para %s", asteroid_name)
        return None


def keplerian_to_cartesian(a, e, i, omega, Omega, nu):
    i_rad = math.radians(i)
    omega_rad = math.radians(omega)
    Omega_rad = math.radians(Omega)
    nu_rad = math.radians(nu)

    r = (a * (1 - e**2)) / (1 + e * math.cos(nu_rad))

    cos_Omega = math.cos(Omega_rad)
    sin_Omega = math.sin(Omega_rad)
    cos_i = math.cos(i_rad)
    sin_i = math.sin(i_rad)
    cos_omega_nu = math.cos(omega_rad + nu_rad)
    sin_omega_nu = math.sin(omega_rad + nu_rad)

    x = r * (cos_Omega * cos_omega_nu - sin_Omega * sin_omega_nu * cos_i)
    y = r * (sin_Omega * cos_omega_nu + cos_Omega * sin_omega_nu * cos_i)
    z = r * (sin_omega_nu * sin_i)

    return round(r, 6), round(x, 6), round(y, 6), round(z, 6)


def extract_sbdb_info(sbdb_data):
    empty_info = {
        "inclination": 0.0,
        "earth_distance_au": 0.0,
        "coordinates": {"r_au": 0.0, "x_au": 0.0, "y_au": 0.0, "z_au": 0.0},
    }

    if not sbdb_data:
        return empty_info

    try:
        elements_dict = {}
        elements = sbdb_data.get("orbit", {}).get("elements", [])

        for element in elements:
            element_name = element.get("name")
            element_value = float(element.get("value", 0))
            elements_dict[element_name] = element_value

        inclination_value = elements_dict.get("i", 0)
        normalized_inclination = min(inclination_value / 90.0, 1.0)
        inclination = round(normalized_inclination, 4)

        r, x, y, z = 0.0, 0.0, 0.0, 0.0

        required_elements = ["a", "e", "i", "w", "om", "ma"]
        if all(elem in elements_dict for elem in required_elements):
            a = elements_dict["a"]
            e = elements_dict["e"]
            i = elements_dict["i"]
            omega = elements_dict["w"]
            Omega = elements_dict["om"]
            nu = elements_dict["ma"]

            r, x, y, z = keplerian_to_cartesian(a, e, i, omega, Omega, nu)

        moid_au = float(sbdb_data.get("orbit", {}).get("moid", 0))

        return {
            "inclination": inclination,
            "earth_distance_au": moid_au,
            "coordinates": {"r_au": r, "x_au": x, "y_au": y, "z_au": z},
        }
    except (KeyError, ValueError, TypeError):
        return empty_info


@router.head("/{fecha_consulta}")
async def preview_asteroid_head(fecha_consulta: str):
    return Response(status_code=200)


@router.get("/{fecha_consulta}")
async def preview_asteroid(fecha_consulta: date):
    fecha_str = fecha_consulta.strftime("%Y-%m-%d")
    cache_key = get_cache_key(fecha_str)
    cached_data = cache.get(cache_key)

    if cached_data:
        return JSONResponse(
            content=jsonable_encoder({**cached_data, "source": "cache"}),
            headers={"X-Cache": "HIT"},
        )

    params = {
        "start_date": fecha_str,
        "end_date": fecha_str,
        "api_key": NASA_API_KEY,
    }

    try:
        response = requests.get(
            API_NEO_FEED_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        asteroides_del_dia = data.get("near_earth_objects", {}).get(fecha_str, [])

        if not asteroides_del_dia:
            response_data = {
                "fecha_consultada": fecha_str,
                "cantidad": 0,
                "asteroides": [],
                "source": "nasa_api",
            }
            cache.set(cache_key, response_data, EMPTY_RESULT_CACHE_EXPIRE)
            return JSONResponse(
                content=jsonable_encoder(response_data),
                headers={"X-Cache": "MISS"},
            )

        resultados_formateados = []
        for asteroide in asteroides_del_dia:
            nombre = asteroide.get("name")
            diametros_km = asteroide.get("estimated_diameter", {}).get("kilometers", {})
            diametro_min = diametros_km.get("estimated_diameter_min")
            diametro_max = diametros_km.get("estimated_diameter_max")

            if nombre and diametro_min is not None and diametro_max is not None:
                diametro_promedio_km = (diametro_min + diametro_max) / 2
                diametro_promedio_m = diametro_promedio_km * 1000

                approach_data = asteroide.get("close_approach_data", [])
                velocidad_km_s = 0.0
                if approach_data:
                    relative_velocity = approach_data[0].get("relative_velocity", {})
                    velocidad_km_s = float(
                        relative_velocity.get("kilometers_per_second", 0)
                    )

                sbdb_data = get_sbdb_data(nombre)
                sbdb_info = extract_sbdb_info(sbdb_data)
                earth_distance_m = sbdb_info["earth_distance_au"] * 149597870700

                resultados_formateados.append(
                    {
                        "id": asteroide.get("id"),
                        "nombre": nombre,
                        "diametro_promedio_m": round(diametro_promedio_m, 2),
                        "velocidad_km_s": round(velocidad_km_s, 4),
                        "altura_tierra_m": round(earth_distance_m, 2),
                        "inclinacion": sbdb_info["inclination"],
                        "coordenadas": sbdb_info["coordinates"],
                    }
                )

        response_data = {
            "fecha_consultada": fecha_str,
            "cantidad": len(resultados_formateados),
            "asteroides": resultados_formateados,
            "source": "nasa_api",
        }
        cache.set(cache_key, response_data, CACHE_EXPIRE)

        return JSONResponse(
            content=jsonable_encoder(response_data),
            headers={"X-Cache": "MISS"},
        )
    except requests.exceptions.HTTPError as exc:
        logger.exception("Error HTTP al consultar la API NEO de NASA")
        status_code = exc.response.status_code if exc.response is not None else 502
        if status_code == 429:
            detail = "Se alcanzó el límite de consultas de la API de NASA."
        else:
            detail = "La API de NASA devolvió un error al consultar los asteroides."
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except requests.exceptions.RequestException as exc:
        logger.exception("Error de conexión al consultar la API NEO de NASA")
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar con la API de NASA.",
        ) from exc
    except Exception as exc:
        logger.exception("Error interno al generar el preview de asteroides")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor.",
        ) from exc


@router.delete(
    "/cache/{fecha_consulta}",
    dependencies=[Depends(require_cache_admin)],
)
async def clear_preview_cache(fecha_consulta: str):
    cache_key = get_cache_key(fecha_consulta)
    if cache.delete(cache_key):
        return {"message": f"Caché de la fecha {fecha_consulta} limpiado correctamente"}

    raise HTTPException(status_code=500, detail="No se pudo limpiar el caché")
