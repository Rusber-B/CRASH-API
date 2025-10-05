import requests
import os
import math
from datetime import date
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/previewAsteroid", tags=["Preview Asteroid"])

API_NEO_FEED_URL = "https://api.nasa.gov/neo/rest/v1/feed"
API_SBDB_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api"
NASA_API_KEY = os.getenv("apiKey")

def clean_asteroid_name(name: str) -> str:
    """Limpia el nombre del asteroide removiendo paréntesis"""
    return name.replace("(", "").replace(")", "")

def get_sbdb_data(asteroid_name: str):
    """Obtiene datos del asteroide desde la API SBDB de JPL"""
    try:
        clean_name = clean_asteroid_name(asteroid_name)
        url = f"{API_SBDB_URL}?sstr={clean_name}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def keplerian_to_cartesian(a, e, i, omega, Omega, nu):
    """
    Convierte elementos keplerianos a coordenadas cartesianas (x, y, z)
    
    Parámetros:
    a: semieje mayor (AU)
    e: excentricidad
    i: inclinación (grados)
    omega: argumento del periastro (grados)
    Omega: longitud del nodo ascendente (grados)
    nu: anomalía verdadera (grados)
    
    Retorna:
    r, x, y, z (en AU)
    """
    # Convertir grados a radianes
    i_rad = math.radians(i)
    omega_rad = math.radians(omega)
    Omega_rad = math.radians(Omega)
    nu_rad = math.radians(nu)
    
    # Calcular distancia radial
    r = (a * (1 - e**2)) / (1 + e * math.cos(nu_rad))
    
    # Calcular coordenadas en el plano orbital
    x_p = r * math.cos(nu_rad)
    y_p = r * math.sin(nu_rad)
    
    # Aplicar rotaciones 3-1-3
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
    """Extrae información relevante y calcula coordenadas cartesianas"""
    if not sbdb_data:
        return {
            "inclination": 0.0, 
            "earth_distance_au": 0.0,
            "coordinates": {"r": 0.0, "x": 0.0, "y": 0.0, "z": 0.0}
        }
    
    try:
        # Extraer elementos keplerianos
        elements_dict = {}
        elements = sbdb_data.get("orbit", {}).get("elements", [])
        
        for element in elements:
            element_name = element.get("name")
            element_value = float(element.get("value", 0))
            elements_dict[element_name] = element_value
        
        # Extraer inclinación para el campo existente
        inclination_value = elements_dict.get("i", 0)
        normalized_inclination = min(inclination_value / 90.0, 1.0)
        inclination = round(normalized_inclination, 4)
        
        # Calcular coordenadas cartesianas si tenemos todos los elementos necesarios
        r, x, y, z = 0.0, 0.0, 0.0, 0.0
        
        required_elements = ["a", "e", "i", "w", "om", "ma"]
        if all(elem in elements_dict for elem in required_elements):
            # Usar anomalía media (ma) como aproximación de anomalía verdadera (nu)
            # En una implementación más precisa, se debería convertir ma a nu
            a = elements_dict["a"]  # semieje mayor (AU)
            e = elements_dict["e"]  # excentricidad
            i = elements_dict["i"]  # inclinación (grados)
            omega = elements_dict["w"]  # argumento del periastro (grados)
            Omega = elements_dict["om"]  # longitud nodo ascendente (grados)
            nu = elements_dict["ma"]  # usar anomalía media como aproximación (grados)
            
            r, x, y, z = keplerian_to_cartesian(a, e, i, omega, Omega, nu)
        
        # Para la distancia a la Tierra, usar el MOID
        moid_au = float(sbdb_data.get("orbit", {}).get("moid", 0))
        
        return {
            "inclination": inclination,
            "earth_distance_au": moid_au,
            "coordinates": {
                "r_au": r,
                "x_au": x,
                "y_au": y,
                "z_au": z
            }
        }
    except (KeyError, ValueError, TypeError) as e:
        return {
            "inclination": 0.0, 
            "earth_distance_au": 0.0,
            "coordinates": {"r_au": 0.0, "x_au": 0.0, "y_au": 0.0, "z_au": 0.0}
        }

@router.get("/{fecha_consulta}")
async def previewAsteroid(fecha_consulta: date):
    """
    Este endpoint recibe una fecha y devuelve información detallada de asteroides.
    
    - **fecha_consulta**: La fecha para la búsqueda en formato **YYYY-MM-DD**.
    """
    fecha_str = fecha_consulta.strftime("%Y-%m-%d")
    params = {"start_date": fecha_str, "end_date": fecha_str, "api_key": NASA_API_KEY}

    try:
        # Obtener datos de la API NEO
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
                # Diámetro promedio en metros
                diametro_promedio_km = (diametro_min + diametro_max) / 2
                diametro_promedio_m = diametro_promedio_km * 1000
                
                # Velocidad relativa (km/s)
                approach_data = asteroide.get("close_approach_data", [])
                velocidad_km_s = 0.0
                if approach_data:
                    relative_velocity = approach_data[0].get("relative_velocity", {})
                    velocidad_km_s = float(relative_velocity.get("kilometers_per_second", 0))
                
                # Obtener datos adicionales de JPL y calcular coordenadas
                sbdb_data = get_sbdb_data(nombre)
                sbdb_info = extract_sbdb_info(sbdb_data)
                
                # Convertir distancia de AU a metros (1 AU = 149,597,870,700 metros)
                earth_distance_m = sbdb_info["earth_distance_au"] * 149597870700
                
                resultados_formateados.append({
                    "id": asteroide.get("id"),
                    "nombre": nombre,
                    "diametro_promedio_m": round(diametro_promedio_m, 2),
                    "velocidad_km_s": round(velocidad_km_s, 4),
                    "altura_tierra_m": round(earth_distance_m, 2),
                    "inclinacion": sbdb_info["inclination"],
                    "coordenadas": sbdb_info["coordinates"]
                })
        
        return {
            "fecha_consultada": fecha_str,
            "cantidad": len(resultados_formateados),
            "asteroides": resultados_formateados
        }
        
    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(
            status_code=http_err.response.status_code, 
            detail=f"Error HTTP del API de la NASA: {http_err}"
        )
    except requests.exceptions.RequestException as req_err:
        raise HTTPException(
            status_code=503, 
            detail=f"Error de conexión con el API de la NASA: {req_err}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno del servidor: {str(e)}"
        )