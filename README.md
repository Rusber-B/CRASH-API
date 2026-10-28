# CRASH API

API construida con FastAPI para consultar información de asteroides cercanos a la Tierra usando las APIs públicas de NASA y JPL.

## Características

- Consulta de asteroides por fecha mediante NASA NeoWs.
- Detalle de un asteroide por su ID.
- Cálculo de coordenadas orbitales aproximadas con datos de JPL SBDB.
- Caché con Redis y fallback automático a memoria.
- CORS configurable.
- Endpoints administrativos de caché protegidos por token.

## Requisitos

- Python 3.11 o superior.
- Una API key gratuita de NASA: https://api.nasa.gov/

## Instalación local

```powershell
git clone https://github.com/Rusber-B/CRASH-API.git
cd CRASH-API
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env` y configura al menos `NASA_API_KEY`.

```powershell
uvicorn main:app --reload
```

La documentación interactiva queda disponible en http://127.0.0.1:8000/docs.

## Variables de entorno

| Variable | Obligatoria | Descripción |
| --- | --- | --- |
| `NASA_API_KEY` | Sí | API key de NASA. |
| `PORT` | No | Puerto para ejecutar `main.py` directamente. Por defecto `8000`. |
| `CORS_ORIGINS` | No | Orígenes permitidos separados por coma, sin barra final. Por defecto `https://crashnasa.vercel.app`. |
| `REDIS_URL` | No | URL completa de Redis, por ejemplo `redis://usuario:clave@host:6379/0`. |
| `REDIS_HOST` | No | Host de Redis si no se usa `REDIS_URL`. Por defecto `localhost`. |
| `REDIS_PORT` | No | Puerto de Redis. Por defecto `6379`. |
| `REDIS_DB` | No | Base de datos de Redis. Por defecto `0`. |
| `REDIS_PASSWORD` | No | Contraseña de Redis, si aplica. |
| `CACHE_ADMIN_TOKEN` | No | Token para endpoints administrativos de caché. Si está vacío, esos endpoints responden 404. |

Si no se configura Redis, la aplicación usa caché en memoria y sigue funcionando. En Vercel el caché en memoria no persiste entre invocaciones, por lo que se recomienda configurar `REDIS_URL` (por ejemplo, Upstash Redis).

## Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/` | Información general de la API. |
| `GET` | `/previewAsteroid/{fecha}` | Asteroides de una fecha en formato `YYYY-MM-DD`. |
| `GET` | `/asteroidDetails/{asteroid_id}` | Detalle de un asteroide por ID. |
| `GET` | `/cache/health` | Estado del sistema de caché. |
| `GET` | `/cache/keys` | Lista claves del caché. Requiere token. |
| `GET` | `/cache/info` | Estadísticas del caché. Requiere token. |
| `DELETE` | `/cache/clear` | Limpia claves del caché por patrón. Requiere token. |
| `DELETE` | `/previewAsteroid/cache/{fecha}` | Limpia el caché de una fecha. Requiere token. |
| `DELETE` | `/asteroidDetails/cache/{asteroid_id}` | Limpia el caché de un asteroide. Requiere token. |

Ejemplos:

```text
GET /previewAsteroid/2025-10-04
GET /asteroidDetails/3542519
```

Los endpoints administrativos requieren la cabecera:

```text
X-Admin-Token: <CACHE_ADMIN_TOKEN>
```

## Despliegue en Vercel

| Componente | URL |
| --- | --- |
| Backend (API) | https://crash-apirepsoftware.vercel.app |
| Frontend | https://crashnasa.vercel.app |

El backend se despliega en Vercel. Vercel detecta FastAPI por la instancia `app` de `main.py`, así que no hace falta `vercel.json`.

Configura las variables de entorno en **Project Settings → Environment Variables** (no subas el archivo `.env` al repositorio ni lo adjuntes al proyecto):

| Variable | Valor |
| --- | --- |
| `NASA_API_KEY` | Tu API key de NASA (obligatoria). |
| `CORS_ORIGINS` | `https://crashnasa.vercel.app` |
| `REDIS_URL` | URL pública de Redis (opcional). |
| `CACHE_ADMIN_TOKEN` | Token para endpoints administrativos (opcional). |

Guarda los cambios y pulsa **Redeploy**. En Vercel no se configura `PORT`: la función expone la aplicación directamente.

El archivo `render.yaml` se conserva únicamente como referencia de una alternativa de despliegue; el despliegue activo es Vercel.

## Seguridad

- No se versionan archivos `.env`.
- Las claves se leen únicamente desde variables de entorno.
- Los endpoints que permiten limpiar o inspeccionar el caché están protegidos por token.
- Los errores de las APIs externas no devuelven la URL de la petición para evitar filtrar la API key.

## Estructura del proyecto

```text
config/          Configuración centralizada
endpoints/       Rutas de la API
middleware/      Dependencias de autenticación
main.py          Aplicación FastAPI
redis_cache.py   Caché Redis y fallback en memoria
render.yaml      Configuración de despliegue
```
