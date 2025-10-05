import os
from fastapi import FastAPI
from fastapi.responses import Response  # <-- Añadir esta importación
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# --- URLs de APIs y Claves ---
NASA_API_KEY = os.getenv("apiKey")

if not NASA_API_KEY:
    raise RuntimeError("La variable de entorno apiKey no está configurada. Por favor, créala en el archivo .env.")

# Crear la aplicación FastAPI principal
app = FastAPI(
    title="API de Asteroides NASA",
    description="API unificada para consultar datos de asteroides de la NASA",
    version="1.0.0"
)

# Importar los routers desde los archivos de endpoints
from endpoints.PreviewAsteroid import router as preview_router
from endpoints.DetailAsteroid import router as detail_router

# Incluir todos los routers en la app principal
app.include_router(preview_router)
app.include_router(detail_router)

# Endpoint HEAD para la ruta raíz (CORS)
@app.head("/")
def root_head():
    """
    Endpoint HEAD para CORS preflight requests en la ruta raíz.
    """
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, HEAD",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Max-Age": "86400"
        }
    )

# Endpoint raíz unificado (GET)
@app.get("/")
def root():
    return {
        "mensaje": "Bienvenido al API Unificada de Datos de Asteroides de la NASA",
        "documentacion": "/docs",
        "endpoints_disponibles": {
            "preview_asteroid": "/previewAsteroid/{fecha}",
            "asteroid_details": "/asteroidDetails/{nombre}",
            "asteroid_position": "/position/{nombre}"
        },
        "ejemplos_de_uso": [
            {"descripcion": "Ver asteroides por fecha", "url": "/previewAsteroid/2025-10-04"},
            {"descripcion": "Buscar detalles de un asteroide por nombre", "url": "/asteroidDetails/(2008 CK70)"},
            {"descripcion": "Consultar posición y elementos orbitales", "url": "/position/Ceres"}
        ]
    }

# ELIMINA esta parte si vas a usar uvicorn directamente:
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=PORT)