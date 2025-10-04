import requests
import os
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/asteroidDetails", tags=["Asteroid Details"])

API_NEO_BROWSE_URL = "https://api.nasa.gov/neo/rest/v1/neo/browse"
NASA_API_KEY = os.getenv("apiKey")

@router.get("/{nombre_asteroide}")
async def get_asteroid_details(nombre_asteroide: str):
    """
    Busca un asteroide por su nombre y devuelve sus detalles más importantes.
    Este endpoint SOLO busca en la base de datos de Objetos Cercanos a la Tierra (NEO).

    - **nombre_asteroide**: El nombre exacto del asteroide (ej: (2008 CK70)).
    """
    params = {"api_key": NASA_API_KEY}

    try:
        response = requests.get(API_NEO_BROWSE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        todos_los_asteroides = data.get("near_earth_objects", [])

        for asteroide in todos_los_asteroides:
            if asteroide.get("name", "").strip().lower() == nombre_asteroide.strip().lower():
                diametros_km = asteroide.get("estimated_diameter", {}).get("kilometers", {})
                detalles = {
                    "id": asteroide.get("id"),
                    "neo_reference_id": asteroide.get("neo_reference_id"),
                    "name": asteroide.get("name"),
                    "nasa_jpl_url": asteroide.get("nasa_jpl_url"),
                    "absolute_magnitude_h": asteroide.get("absolute_magnitude_h"),
                    "estimated_diameter_km": {
                        "min": diametros_km.get("estimated_diameter_min"),
                        "max": diametros_km.get("estimated_diameter_max")
                    },
                    "is_potentially_hazardous_asteroid": asteroide.get("is_potentially_hazardous_asteroid"),
                    "is_sentry_object": asteroide.get("is_sentry_object"),
                    "close_approach_data": asteroide.get("close_approach_data")
                }
                return detalles

        raise HTTPException(
            status_code=404, 
            detail=f"Asteroide '{nombre_asteroide}' no encontrado en la base de datos de Objetos Cercanos a la Tierra (NEO)."
        )

    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=http_err.response.status_code, detail=f"Error HTTP del API de la NASA: {http_err}")
    except requests.exceptions.RequestException as req_err:
        raise HTTPException(status_code=503, detail=f"Error de conexión con el API de la NASA: {req_err}")