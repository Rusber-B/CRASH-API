import secrets

from fastapi import Header, HTTPException, status

from config.settings import CACHE_ADMIN_TOKEN


def require_cache_admin(x_admin_token: str | None = Header(default=None)) -> None:
    if not CACHE_ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found",
        )

    if not secrets.compare_digest(x_admin_token or "", CACHE_ADMIN_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token de administración inválido",
        )
