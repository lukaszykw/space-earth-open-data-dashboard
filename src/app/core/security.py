import secrets

from fastapi import Header, HTTPException

from app.core.config import settings


async def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    configured_token = settings.admin_api_token
    if configured_token is None:
        raise HTTPException(status_code=503, detail="manual ingestion is disabled")
    if x_admin_token is None or not secrets.compare_digest(
        x_admin_token,
        configured_token.get_secret_value(),
    ):
        raise HTTPException(status_code=401, detail="invalid admin token")
