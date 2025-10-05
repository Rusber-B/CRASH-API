import requests
import os
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/asteroidDetails", tags=["Asteroid Details"])

API_NEO_SEARCH_URL = "https://api.nasa.gov/neo/rest/v1/neo/"
NASA_API_KEY = os.getenv("apiKey")

@router.get("/{asteroid_id}")
async def get_asteroid_details(asteroid_id: str):
    """
    Busca un asteroide por su ID y devuelve información general simplificada.
    Perfecto para personas que no son expertas en astronomía.

    - **asteroid_id**: El ID numérico del asteroide (ej: 3712619)
    """
    try:
        url = f"{API_NEO_SEARCH_URL}{asteroid_id}"
        params = {"api_key": NASA_API_KEY}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        asteroide = response.json()

        # Extraer datos básicos
        diametros_m = asteroide.get("estimated_diameter", {}).get("meters", {})
        diametro_min_m = diametros_m.get("estimated_diameter_min", 0)
        diametro_max_m = diametros_m.get("estimated_diameter_max", 0)
        
        # Calcular el diámetro promedio
        diametro_promedio_m = (diametro_min_m + diametro_max_m) / 2 if diametro_min_m > 0 and diametro_max_m > 0 else 0

        # Procesar datos de acercamiento más reciente
        close_approaches = asteroide.get("close_approach_data", [])
        ultimo_acercamiento = {}
        if close_approaches:
            # Tomar el acercamiento más reciente
            mas_reciente = close_approaches[0]
            ultimo_acercamiento = {
                "fecha": mas_reciente.get("close_approach_date"),
                "velocidad_km_s": round(float(mas_reciente.get("relative_velocity", {}).get("kilometers_per_second", 0)), 2),
                "distancia_km": round(float(mas_reciente.get("miss_distance", {}).get("kilometers", 0)), 2),
                "cuerpo_orbital": mas_reciente.get("orbiting_body")
            }

        return {
            "informacion_basica": {
                "id": asteroide.get("id"),
                "nombre": asteroide.get("name"),
                "enlace_nasa": asteroide.get("nasa_jpl_url"),
                "es_peligroso": asteroide.get("is_potentially_hazardous_asteroid", False),
                "es_monitoreado": asteroide.get("is_sentry_object", False)
            },
            "tamano": {
                "diametro_minimo_metros": round(diametro_min_m, 2),
                "diametro_maximo_metros": round(diametro_max_m, 2),
                "comparacion": f"Aproximadamente {round(diametro_promedio_m, 2)} metros - similar a un edificio de {round(diametro_promedio_m / 3, 0)} pisos" if diametro_promedio_m > 0 else "Tamaño no determinado"
            },
            "ultimo_acercamiento": ultimo_acercamiento,
            "datos_tecnicos": {
                "magnitud_absoluta": asteroide.get("absolute_magnitude_h"),
                "es_peligroso": asteroide.get("is_potentially_hazardous_asteroid", False)
            }
        }

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            raise HTTPException(
                status_code=404, 
                detail=f"Asteroide con ID '{asteroid_id}' no encontrado. Verifica que el ID sea correcto."
            )
        raise HTTPException(
            status_code=http_err.response.status_code, 
            detail=f"Error al consultar los datos de la NASA: {http_err}"
        )
    except requests.exceptions.RequestException as req_err:
        raise HTTPException(
            status_code=503, 
            detail=f"No se pudo conectar con la NASA. Intenta nuevamente más tarde."
        )