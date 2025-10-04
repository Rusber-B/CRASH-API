import requests
import os
from datetime import date
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/previewAsteroid", tags=["Preview Asteroid"])

API_NEO_FEED_URL = "https://api.nasa.gov/neo/rest/v1/feed"
NASA_API_KEY = os.getenv("apiKey")

@router.get("/{fecha_consulta}")
async def previewAsteroid(fecha_consulta: date):
    """
    Este endpoint recibe una fecha y devuelve una lista con el nombre
    y el diámetro promedio en kilómetros de cada asteroide detectado en esa fecha.

    - **fecha_consulta**: La fecha para la búsqueda en formato **YYYY-MM-DD**.
    """
    fecha_str = fecha_consulta.strftime("%Y-%m-%d")
    params = {"start_date": fecha_str, "end_date": fecha_str, "api_key": NASA_API_KEY}

    try:
        response = requests.get(API_NEO_FEED_URL, params=params)
        response.raise_for_status()
        data = response.json()
        asteroides_del_dia = data.get("near_earth_objects", {}).get(fecha_str, [])

        if not asteroides_del_dia:
            return {"fecha_consultada": fecha_str, "cantidad": 0, "asteroides": []}

        resultados_formateados = []
        for asteroide in asteroides_del_dia:
            nombre = asteroide.get("name")
            diametros_km = asteroide.get("estimated_diameter", {}).get("kilometers", {})
            diametro_min = diametros_km.get("estimated_diameter_min")
            diametro_max = diametros_km.get("estimated_diameter_max")
            if nombre and diametro_min is not None and diametro_max is not None:
                diametro_promedio = (diametro_min + diametro_max) / 2
                resultados_formateados.append({
                    "nombre": nombre,
                    "diametro_promedio_km": round(diametro_promedio, 4)
                })
        return {
            "fecha_consultada": fecha_str,
            "cantidad": len(resultados_formateados),
            "asteroides": resultados_formateados
        }
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=http_err.response.status_code, detail=f"Error HTTP del API de la NASA: {http_err}")
    except requests.exceptions.RequestException as req_err:
        raise HTTPException(status_code=503, detail=f"Error de conexión con el API de la NASA: {req_err}")