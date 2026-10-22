from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from config.settings import CORS_ORIGINS, NASA_API_KEY, PORT
from endpoints.Cache import router as cache_router
from endpoints.DetailAsteroid import router as detail_router
from endpoints.PreviewAsteroid import router as preview_router

if not NASA_API_KEY:
    raise RuntimeError(
        "La variable de entorno NASA_API_KEY no está configurada. "
        "Copia .env.example a .env y añade tu clave de NASA."
    )

app = FastAPI(
    title="API de Asteroides NASA",
    description="API unificada para consultar datos de asteroides de la NASA",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(preview_router)
app.include_router(detail_router)
app.include_router(cache_router)


@app.head("/")
def root_head():
    return Response(status_code=200)


@app.get("/")
def root():
    return {
        "mensaje": "Bienvenido al API Unificada de Datos de Asteroides de la NASA",
        "documentacion": "/docs",
        "endpoints_disponibles": {
            "preview_asteroid": "/previewAsteroid/{fecha}",
            "asteroid_details": "/asteroidDetails/{asteroid_id}",
            "cache_health": "/cache/health",
        },
        "ejemplos_de_uso": [
            {
                "descripcion": "Ver asteroides por fecha",
                "url": "/previewAsteroid/2025-10-04",
            },
            {
                "descripcion": "Buscar detalles de un asteroide por ID",
                "url": "/asteroidDetails/3542519",
            },
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
