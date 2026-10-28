import os

from dotenv import load_dotenv

load_dotenv()


def get_env(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value and value.strip():
            return value.strip()
    return default


def get_port(default: int = 8000) -> int:
    try:
        return int(get_env("PORT", default=str(default)))
    except (TypeError, ValueError):
        return default


NASA_API_KEY = get_env("NASA_API_KEY", "apiKey")
PORT = get_port()

DEFAULT_CORS_ORIGINS = "https://crashnasa.vercel.app"

_raw_origins = get_env("CORS_ORIGINS", default=DEFAULT_CORS_ORIGINS) or DEFAULT_CORS_ORIGINS
CORS_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in _raw_origins.split(",")
    if origin.strip()
]

CACHE_ADMIN_TOKEN = get_env("CACHE_ADMIN_TOKEN")
