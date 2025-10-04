import os
from fastapi import FastAPI
import sys
import os
import uvicorn

# --- URLs de APIs y Claves ---
API_NEO_URL = "https://api.nasa.gov/neo/rest/v1/feed"
API_JPL_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api"
NASA_API_KEY = os.getenv("NASA_API_KEY") # Obtiene la clave del .env


# Agregar la carpeta endpoints al path si es necesario
sys.path.append(os.path.dirname(__file__))

from endpoints.PreviewAsteroid import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)