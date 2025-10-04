import requests
import uvicorn
import os
from datetime import date
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# --- 1. Inicialización de la Aplicación y Configuración ---
app = FastAPI(
    title="NASA Asteroid Data API",
    description="Una API para obtener el nombre y diámetro promedio de los Objetos Cercanos a la Tierra (NEO) para una fecha específica.",
    version="2.1.0"
)

# --- 2. URLs de APIs y Claves (leídas desde el entorno) ---
API_NEO_URL = "https://api.nasa.gov/neo/rest/v1/feed"
NASA_API_KEY = os.getenv("apiKey")  # Obtiene la clave del .env

# Verificación de seguridad: nos aseguramos de que la API Key exista
if not NASA_API_KEY:
    raise RuntimeError("La variable de entorno apiKey no está configurada. Por favor, créala en el archivo .env.")



# --- 3. Endpoints de la API ---

@app.get("/previewAsteroid/{fecha_consulta}")
async def previewAsteroid(fecha_consulta: date):
    """
    Este endpoint recibe una fecha y devuelve una lista con el nombre
    y el diámetro promedio en kilómetros de cada asteroide.

    - **fecha_consulta**: La fecha para la búsqueda en formato **YYYY-MM-DD**.
    """
    fecha_str = fecha_consulta.strftime("%Y-%m-%d")

    params = {
        "start_date": fecha_str,
        "end_date": fecha_str,
        "api_key": NASA_API_KEY  # Usar la variable correcta
    }

    try:
        response = requests.get(API_NEO_URL, params=params)
        response.raise_for_status()  # Lanza una excepción para errores HTTP (4xx o 5xx)

        data = response.json()
        asteroides_del_dia = data.get("near_earth_objects", {}).get(fecha_str, [])

        if not asteroides_del_dia:
            return {"fecha_consultada": fecha_str, "cantidad": 0, "asteroides": []}

        # Procesar cada asteroide para extraer la información necesaria
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

        # Devolver la lista de resultados formateados
        return {
            "fecha_consultada": fecha_str,
            "cantidad": len(resultados_formateados),
            "asteroides": resultados_formateados
        }

    except requests.exceptions.HTTPError as http_err:
        raise HTTPException(status_code=http_err.response.status_code, detail=f"Error HTTP del API de la NASA: {http_err}")
    except requests.exceptions.RequestException as req_err:
        raise HTTPException(status_code=503, detail=f"Error de conexión con el API de la NASA: {req_err}")

@app.get("/")
def root():
    return {
        "mensaje": "Bienvenido al API de Datos de Asteroides",
        "documentacion": "/docs",
        "ejemplo_de_uso": "/previewAsteroid/2025-10-04"
    }

# --- 4. Ejecución del Servidor ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)