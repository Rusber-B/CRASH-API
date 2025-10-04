import requests
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/position", tags=["Asteroid Position"])

API_SBDB_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api"

@router.get("/{asteroid_name}")
async def get_asteroid_position_data(asteroid_name: str):
    """
    Este endpoint busca un objeto celeste (asteroide, cometa) por su nombre
    y devuelve sus elementos orbitales.

    - **asteroid_name**: El nombre o designación del objeto a buscar (ej: 'Ceres', '2015 AC45').
    """
    params = {
        "sstr": asteroid_name
    }

    try:
        response = requests.get(API_SBDB_URL, params=params)
        response.raise_for_status()

        data = response.json()

        if data.get("message") == "no object found":
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró ningún objeto con el nombre '{asteroid_name}'."
            )

        orbit_data = data.get("orbit", {})
        elements = orbit_data.get("elements", [])
        
        if not orbit_data or not elements:
            raise HTTPException(
                status_code=404,
                detail=f"Se encontró el objeto '{asteroid_name}', pero no tiene datos orbitales disponibles."
            )
            
        formatted_elements = {
            elem.get("name"): {
                "value": elem.get("value"), 
                "units": elem.get("units"),
                "label": elem.get("label"),
                "title": elem.get("title")
            } for elem in elements
        }

        return {
            "object_info": {
                "name": data.get("object", {}).get("fullname"),
                "designation": data.get("object", {}).get("des"),
            },
            "orbital_epoch": orbit_data.get("epoch"),
            "epoch_description": "La fecha (en Tiempo Juliano) para la cual estos elementos orbitales son válidos.",
            "elements": formatted_elements
        }

    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(
            status_code=http_err.response.status_code,
            detail=f"Error HTTP del API de JPL: {http_err}"
        )
    except requests.exceptions.RequestException as req_err:
        raise HTTPException(
            status_code=503,
            detail=f"Error de conexión con el API de JPL: {req_err}"
        )